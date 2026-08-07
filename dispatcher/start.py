"""Start Async Bifrost."""

import asyncio
import importlib
import logging
import pkgutil
from pathlib import Path

import aiosqlite

from . import protocols
from .core.api import BifrostAPI
from .core.device_registry import DeviceRegistry
from .core.history import History
from .core.state_machine import StateMachine
from .engine.flow_runner import FlowRunner
from .settings import Settings

_LOGGER = logging.getLogger(__name__)


async def initialize_db(db_path: Path, schema_path: Path):
    """Inicializa o banco de dados."""
    if not schema_path.exists():
        _LOGGER.error(
            "Arquivo de schema do banco de dados não encontrado: %s", schema_path
        )
        return

    try:
        schema_sql = schema_path.read_text(encoding="utf-8")

        async with aiosqlite.connect(db_path) as db:
            await db.executescript(schema_sql)
            await db.commit()
            _LOGGER.info("Banco de dados iniciado: %s", db_path)

    except Exception:
        _LOGGER.exception("Erro fatal ao inicializar banco de dados: %s", db_path)


async def discover_protocols(config_dir: Path, settings: Settings):
    """Descobre e faz a importação de todos os protocolos, só faz setup dos que estão configurados."""
    _LOGGER.debug("Descobrindo Protocolos...")

    for loader, module_name, is_pkg in pkgutil.iter_modules(protocols.__path__):
        _LOGGER.debug("Descoberto módulo %s", module_name)

        try:
            module = importlib.import_module(f"{protocols.__name__}.{module_name}")
        except ModuleNotFoundError as e:
            if e.name == module_name or e.name == f"{protocols.__name__}.{module_name}":
                _LOGGER.warning(
                    "Erro de caminho> Não conseguiu achar o arquivo %s.", module_name
                )
            else:
                _LOGGER.error(
                    "ERRO INTERNO em %s: O módulo existe, mas falhou ao carregar: %s",
                    module_name,
                    e.name,
                )
            continue

        # Só prossegue se tiver uma função setup protocol
        if hasattr(module, "setup_protocol"):
            _LOGGER.debug("O módulo %s tem uma função de setup", module_name)
            conf = getattr(settings, module_name, None)

            if conf:
                _LOGGER.info(
                    "Existe uma configuração para o módulo %s, inicando uma task assíncrona",
                    module_name,
                )
                asyncio.create_task(module.setup_protocol(config_dir, conf))
        else:
            _LOGGER.debug("Módulo %s não tem uma função de setup!", module_name)
    _LOGGER.info("Finalizou inicialização dos protocolos!")


async def start(config_dir: Path, settings: Settings):
    _LOGGER.info("Inicializando a Bifrost")

    db_path = config_dir / settings.registry_db_path
    schema_path = config_dir / settings.registry_db_schema_path

    # Inicializa o banco de dados SQLite
    await initialize_db(db_path=db_path, schema_path=schema_path)

    # Inicializa o registro de dispositivos
    registry = DeviceRegistry(db_path)

    # Inicializa a state machine e restaura o último estado conhecido de cada dispositivo
    state_machine = StateMachine(db_path)
    await state_machine.restore()

    # Inicia o Flow Engine com as automações definidas em automations.json
    flow_runner = FlowRunner(config_dir / settings.automations_path, registry)
    await flow_runner.start()

    # Inicia a API
    api = BifrostAPI(
        host=settings.api["host"],
        port=settings.api["port"],
        registry=registry,
        state_machine=state_machine,
        flow_runner=flow_runner,
    )
    await api.start()

    # Inicia o histório via SQLite
    history = History(db_path)
    history.start()

    # Faz a descoberta, configuração e inicialização dos protocolos
    await discover_protocols(config_dir, settings)

    _LOGGER.info("Bifrost Iniciada!")
    await asyncio.Future()
