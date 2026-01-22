"""Start Async Bifrost."""

import asyncio
import importlib
import logging
import pkgutil
from pathlib import Path

from . import protocols
from .core.device_registry import DeviceRegistry
from .core.router import Router
from .settings import Settings


_LOGGER = logging.getLogger(__name__)


async def discover_protocols(config_dir: Path, settings: Settings):
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

    # Inicia o roteamento de mensagens
    router = Router(registry)
    
    # Faz a descoberta, configuração e inicialização dos protocolos
    await discover_protocols(config_dir, settings)

    _LOGGER.info("Bifrost Iniciada!")
    await asyncio.Future()