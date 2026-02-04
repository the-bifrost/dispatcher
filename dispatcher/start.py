"""Start Async Bifrost."""

import asyncio
import importlib
import logging
import pkgutil
from pathlib import Path

from . import protocols
from .core.device_registry import DeviceRegistry
from .core.router import Router
from .core.history import HistoryLogger
from .settings import Settings


_LOGGER = logging.getLogger(__name__)

async def init_sqlite():
    pass


async def discover_protocols(config_dir: Path, settings: Settings):
    """Descobre e faz a importação de todos os protocolos, só faz setup dos que estão configurados."""
    _LOGGER.debug("Descobrindo Protocolos...")

    for loader, module_name, is_pkg in pkgutil.iter_modules(protocols.__path__):

        _LOGGER.debug("Descoberto módulo %s", module_name)

        try:
            module = importlib.import_module(f"{protocols.__name__}.{module_name}")
        except ModuleNotFoundError as e:
            if e.name == module_name or e.name == f"{protocols.__name__}.{module_name}":
                _LOGGER.warning("Erro de caminho> Não conseguiu achar o arquivo %s.", module_name)
            else:
                _LOGGER.error("ERRO INTERNO em %s: O módulo existe, mas falhou ao carregar: %s", module_name, e.name)
            continue

        
        # Só prossegue se tiver uma função setup protocol
        if hasattr(module, "setup_protocol"):
            _LOGGER.debug("O módulo %s tem uma função de setup", module_name)
            conf = getattr(settings, module_name, None)

            if conf:
                _LOGGER.info("Existe uma configuração para o módulo %s, inicando uma task assíncrona", module_name)
                asyncio.create_task(module.setup_protocol(config_dir, conf))
        else:
            _LOGGER.debug("Módulo %s não tem uma função de setup!", module_name)
    _LOGGER.info("Finalizou inicialização dos protocolos!")
    

async def start(config_dir: Path, settings: Settings):
    _LOGGER.info("Inicializando a Bifrost")

    # inicializa o registro de dispositivos
    registry = DeviceRegistry(
        db_path=config_dir / settings.registry_db_path, 
        schema_path=config_dir / settings.registry_db_schema_path)
    
    await registry.initialize()

    # Inicia o histório via SQLite
    history_logger = HistoryLogger(config_dir / settings.registry_db_path)

    # Inicia o roteamento de mensagens
    router = Router(registry)
    
    # Faz a descoberta, configuração e inicialização dos protocolos
    await discover_protocols(config_dir, settings)

    _LOGGER.info("Bifrost Iniciada!")
    await asyncio.Future()