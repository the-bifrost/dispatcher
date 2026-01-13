"""Protocolo LoRa que herda de BaseSerialProtocol."""
import asyncio
import logging

import serial_asyncio
from pydantic import BaseModel

from protocols.serial import BaseSerialProtocol


_LOGGER = logging.getLogger(__name__)


class LoraConfig(BaseModel):
    """Configs padrão do protocolo LoRa."""
    port: str
    baudrate: int = 9600


class LoraProtocol(BaseSerialProtocol):
    def __init__(self):
        super().__init__(protocol_name="lora")


async def setup_protocol(raw_config: dict):
    """Faz o setup assíncrono do LoRa."""
    
    # Carrega configurações
    try:
        config = LoraConfig(**raw_config)
    except (TypeError, ValueError) as e:
        _LOGGER.error(f"Erro de validação [{type(e).__name__}]: {e.__cause__}")
        return
    
    # Pega o loop atual
    loop = asyncio.get_event_loop()

    _LOGGER.info("Iniciando LoRa na porta %s a %sbps", config.port, config.baudrate)

    transport, protocol = await serial_asyncio.create_serial_connection(
        loop,
        LoraProtocol,
        config.port,
        config.baudrate
    )

    return protocol
