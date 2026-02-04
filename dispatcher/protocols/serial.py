"""Protocolo Base para Conexões que dependem de Serial."""
import asyncio
import logging
from typing import Optional, cast

from ..core.event_bus import event_bus
from ..core.events import Events
from ..core.envelope import Envelope, parse_envelope
from ..utils.device import Device

_LOGGER = logging.getLogger(__name__)


class BaseSerialProtocol(asyncio.Protocol):
    """Classe base para qualquer protocolo serial na Bifrost."""

    def __init__(self, protocol_name: str):
        self.protocol_name = protocol_name
        self.transport: Optional[asyncio.Transport] = None
        self._buffer = b""

    def connection_made(self, transport) -> None:
        """Salva a conexão e registra callbacks, caso a conexão for bem sucedida."""
        self.transport = cast(asyncio.Transport, transport)
        _LOGGER.info("[%s] Porta aberta: %s", self.protocol_name, transport.get_extra_info('name'))

        # Registra nos eventos do EventBus
        event_bus.subscribe(f"{Events.Protocol.SEND_PREFIX}{self.protocol_name.lower()}", self.handle_event)

    def data_received(self, data: bytes) -> None:
        """Calback acionado de forma assíncrona pelo event loop."""
        self._buffer += data

        if b'\n' in self._buffer:
            lines = self._buffer.split(b'\n')
            self._buffer = lines.pop()

            for line in lines:
                decoded_line = line.decode(errors='ignore').strip()

                if decoded_line:
                    envelope = parse_envelope(decoded_line)

                    if envelope:
                        asyncio.create_task(event_bus.publish(Events.Protocol.RECEIVED, envelope))

                    else:
                        _LOGGER.warning("[%s] JSON Inválido ou fora do envelope: %s", self.protocol_name, decoded_line)


    async def handle_event(self, data: dict):
        """Recebe dados do EventBus e envia para a Serial."""
        
        envelope: Envelope | None = data.get("envelope")
        device: Device | None = data.get("device")

        if not envelope or not device:
            _LOGGER.warning("Dados incompletos para roteamento: %s", data)
            return
        
        envelope.dst = device.config

        if self.transport:
            message = envelope.model_dump_json() + "\n"
            self.transport.write(message.encode())
            _LOGGER.debug("[%s] Enviado via serial: %s", self.protocol_name, message.strip())

    def connection_lost(self, exc: Exception | None) -> None:
        """Lida com problemas de conexão."""
        _LOGGER.error("[%s] Porta Serial Fechada: %s", self.protocol_name, exc)        