"""Handler LoRa para enviar e receber dados sobre Serial."""

import logging

from .base_serial_handler import BaseSerialHandler

from dispatcher.models.devices import Device, LoraDevice
from dispatcher.utils.envelope import Envelope


_LOGGER = logging.getLogger(__name__)


class LoRaHandler(BaseSerialHandler):
    """Implementação do protocolo LoRa sobre Serial."""

    @property
    def protocol(self) -> str:
        return "lora"
    
    @property
    def address_field(self) -> str:
        return "device_id"
    
    # __init__, start, read e close já estão implementados
    
    async def write(self, envelope: Envelope, device: Device) -> bool:
        """Implementa a lógica de escrita específica para EspNow."""

        if not isinstance(device, LoraDevice):
            _LOGGER.error("Tipo de dispositivo incorreto. Esperado: LoraDevice, Recebido: %s", type(device).__name__)
            return False
        
        json_envelope = envelope.model_dump_json()

        # Escreve usando o método do pai
        return await self._send_string(json_string=json_envelope)
        


