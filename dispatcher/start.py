"""Start Async Bifrost."""

import asyncio
import logging
import importlib
import pkgutil

import protocols
from settings import Settings


_LOGGER = logging.getLogger(__name__)


async def discover_protocols(settings: Settings):
    """Descobre e faz a importação de todos os protocolos, mesmo que não esteja configurado."""
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
                _LOGGER.debug("Existe uma configuração para o módulo %s, inicando uma task assíncrona", module_name)
                asyncio.create_task(module.setup_protocol(conf))
        else:
            _LOGGER.debug("Módulo %s não tem uma função de setup!", module_name)


async def start(settings: Settings):
    _LOGGER.debug("Inicializando a Bifrost")


    _LOGGER.debug("Carregando Protocolos")
    await discover_protocols(settings)

    _LOGGER.debug("Bifrost Iniciada!")
    await asyncio.Future()