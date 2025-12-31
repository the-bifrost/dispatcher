"""Start Async Bifrost."""

import asyncio
import logging
import importlib
import pkgutil

import protocols
from settings import Settings


_LOGGER = logging.getLogger(__name__)


async def discover_protocols(settings: Settings):
    for loader, module_name, is_pkg in pkgutil.iter_modules(protocols.__path__):
        module = importlib.import_module(f"dispatcher.protocols.{module_name}")

        if hasattr(module, "setup_protocol"):
            conf = getattr(settings, module_name, None)

            if conf:
                asyncio.create_task(module.setup_protocol(conf))


async def start(settings: Settings):
    _LOGGER.debug("Inicializando a Bifrost")


    _LOGGER.debug("Carregando Protocolos")
    await discover_protocols(settings)

    _LOGGER.debug("Bifrost Iniciada!")
    await asyncio.Future()