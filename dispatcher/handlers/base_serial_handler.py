"""Classe base para Handlers que utilizam comunicação serial assíncrona"""

import asyncio
import logging

import serial_asyncio

from dispatcher.models.devices import Device, EspNowDevice
from dispatcher.utils.envelope import Envelope, parse_envelope
from dispatcher.handlers import BaseHandler

_LOGGER = logging.getLogger(__name__)

class BaseSerialHandler(BaseHandler):
    """
    Abstrai a lógica comum de conexão, leitura e escrita 
    para dispositivos que se comunicam via serial.
    """

    def __init__(self, port: str, baudrate: int):
        """Prepara os parâmetros da conexão serial."""
        self.port = port
        self.baudrate = baudrate
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None

    async def start(self):
        """Implementação comum para abrir a conexão serial."""

        try:
            self.reader, self.writer = await serial_asyncio.open_serial_connection(
                url=self.port, baudrate=self.baudrate
            )
            _LOGGER.info("Conexão serial com a porta '%s' @ %dbps estabelecida.", self.port, self.baudrate)
        except Exception as e:
            _LOGGER.error("Falha ao abrir a porta serial %s: %s", self.port, e)
            raise
    
    async def read(self) -> Envelope | None:
        """Implementação comum para ler e decodificar uma linha da serial."""

        if not self.reader:
            return None

        try:
            raw_bytes = await asyncio.wait_for(self.reader.readline(), timeout=1.0)
            raw_str = raw_bytes.decode('utf-8', errors='ignore').strip()

            if not raw_str or len(raw_str) < 3 or not (raw_str.startswith('{') and raw_str.endswith('}')):
                return None
            
            return parse_envelope(raw_str)
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            _LOGGER.warning("Erro ao ler da porta serial %s: %s", self.port, e)
            return None

    async def _send_string(self, json_string: str):
        """Método auxiliar para enviar uma string formatada para a serial."""

        if not self.writer:
            return False
        try:
            self.writer.write(json_string.encode('utf-8') + b'\n')
            await self.writer.drain()
            _LOGGER.info("Enviado para '%s': '%s'", self.port, json_string)
            return True
        except Exception as e:
            _LOGGER.error("Falha ao enviar para a porta '%s': %s", self.port, e)
            return False

    async def close(self):
        """Implementação comum para fechar a conexão serial."""
        if self.writer:
            self.writer.close()
            _LOGGER.info("Conexão serial com '%s' fechada.", self.port)