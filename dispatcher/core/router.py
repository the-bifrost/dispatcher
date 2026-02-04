"""Roteador de Mensagem. Lê as mudanças de estado e direciona as mensagens para seu destino correto."""

import logging

from ..core.device_registry import DeviceRegistry
from ..core.event_bus import event_bus
from ..core.events import Events
from ..utils.device import Device
from ..core.envelope import Envelope


_LOGGER = logging.getLogger(__name__)


class Router:
    def __init__(self, registry: DeviceRegistry):
        _LOGGER.info("Iniciando Router de Mensagens.")

        self.registry = registry

        # O Router só ouve mensagens que já foram aprovadas pelo Registry
        event_bus.subscribe(Events.Device.VALIDATED, self.route_message)

        _LOGGER.info("Sucesso ao iniciar o Router!")

    async def route_message(self, data: dict):
        """Recebe um dicionário contendo o envelope e os dados do dispositivo."""

        envelope: Envelope | None = data.get("envelope")
        device: Device | None = data.get("device")

        if not envelope:
            _LOGGER.warning("Recebeu um envelope inválido")
            return
        
        if not device:
            _LOGGER.warning("Recebeu um dispositivo inválido")
            return
        
        
        device_destino: Device | None = await self.registry.get_device(envelope.dst)

        if not device_destino:
            _LOGGER.debug("Dispositivo destino não cadastrado.")
            return


        if envelope.type == "state":
            await self.route_state_message(envelope, device_destino)


    async def route_state_message(self, envelope: Envelope, device_destino: Device):
        """
        Dispara o evento de mudança de estado no protocolo correto.

        Os protocolos devem estar ouvindo "protocol.send_to." + protocol_name 
        Ex: protocol.send_to.mqtt, protocol.send_to.lora
        """
        target_protocol = device_destino.protocol
        event_topic = f"{Events.Protocol.SEND_PREFIX}{target_protocol}"

        _LOGGER.info("Roteando mensagem de '%s' para protocolo '%s'", envelope.src, target_protocol)
        await event_bus.publish(event_topic, envelope)



