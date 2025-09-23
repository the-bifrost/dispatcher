"""Looping Assíncrono da Bifrost."""

import asyncio
import logging
import logging.config
import signal
from typing import Dict, List

from pathlib import Path

_LOGGER = logging.getLogger(__name__)

async def start(config_path):
    """ Prepara e executa o serviço Dispatcher."""
    pass