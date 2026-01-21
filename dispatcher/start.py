"""Start Async Bifrost."""

import asyncio
import importlib
import logging
import pkgutil
from pathlib import Path

import protocols
from core.device_registry import DeviceRegistry
from core.router import Router
from settings import Settings


_LOGGER = logging.getLogger(__name__)


async def discover_protocols(settings: Settings):
    """Descobre e faz a importação de todos os protocolos, só faz setup dos que estão configurados."""
    _LOGGER.debug("Descobrindo Protocolos...")

    for loader, module_name, is_pkg in pkgutil.iter_modules(protocols.__path__):
        _LOGGER.debug("Descoberto módulo %s", module_name)

        try:
            module = importlib.import_module(f"protocols.{module_name}")
        except ModuleNotFoundError as e:
            _LOGGER.warning("Módulo %s não foi encontrado.", module_name)
            continue

        
        # Só prossegue se tiver uma função setup protocol
        if hasattr(module, "setup_protocol"):
            _LOGGER.debug("O módulo %s tem uma função de setup", module_name)
            conf = getattr(settings, module_name, None)

            if conf:
                _LOGGER.info("Existe uma configuração para o módulo %s, inicando uma task assíncrona", module_name)
                asyncio.create_task(module.setup_protocol(conf))
        else:
            _LOGGER.debug("Módulo %s não tem uma função de setup!", module_name)


async def start(config_dir: Path, settings: Settings):
    _LOGGER.info("Inicializando a Bifrost")

    _LOGGER.info("Inicializando o DeviceRegistry")
    registry = DeviceRegistry(
        db_path=config_dir / settings.registry_db_path, 
        schema_path=config_dir / settings.registry_db_schema_path)
    
    await registry.initialize()
    _LOGGER.info("Registry Inicializado!")

    _LOGGER.info("Iniciando Router de Mensagens.")
    router = Router()
    _LOGGER.info("Sucesso ao iniciar o Router!")

    _LOGGER.info("Carregando Protocolos")
    await discover_protocols(settings)
    _LOGGER.info("Finalizou inicialização dos protocolos!")

    _LOGGER.info("Bifrost Iniciada!")
    await asyncio.Future()