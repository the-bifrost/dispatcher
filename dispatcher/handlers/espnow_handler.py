"""Handler ESP-NOW para enviar e receber dados sobre Serial."""

import logging

from .base_serial_handler import BaseSerialHandler

# Importações ANTIGAS
from models.devices import Device, EspNowDevice
from utils.envelope import Envelope

_LOGGER = logging.getLogger(__name__)

class EspNowHandler(BaseSerialHandler):
    """Implementação do protocolo ESP-Now sobre Serial."""

    @property
    def protocol(self) -> str:
        return "espnow"
    
    # __init__, start, read e close já estão implementados
    
    async def write(self, envelope: Envelope, device: Device) -> bool:
        """Implementa a lógica de escrita específica para EspNow."""

        if not isinstance(device, EspNowDevice):
            _LOGGER.error("Tipo de dispositivo incorreto. Esperado: EspNowDevice, Recebido: %s", type(device).__name__)
            return False
        
        # Preparando envelope com a lógica específica do EspNow
        envelope_to_send = envelope.model_copy(deep=True)
        envelope_to_send.dst = device.address
        json_envelope = envelope_to_send.model_dump_json()

        # Escreve usando o método do pai
        return await self._send_string(json_string=json_envelope)
        


