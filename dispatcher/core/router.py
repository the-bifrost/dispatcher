"""Roteador de Mensagem. Lê as mudanças de estado e direciona as mensagens para seu destino correto."""

import logging

from core.event_bus import event_bus
from utils.envelope import Envelope
from utils.const import EventState


_LOGGER = logging.getLogger(__name__)


EVENT_DEVICE_VALIDATED = "device.message_validated"


class Router:
    def __init__(self):
        # O Router só ouve mensagens que já foram aprovadas pelo Registry
        event_bus.subscribe(EVENT_DEVICE_VALIDATED, self.route_message)

    async def route_message(self, data: dict):
        """Recebe um dicionário contendo o envelope e os dados do dispositivo."""

        envelope: Envelope | None = data.get("envelope")

        if envelope:
            target_protocol = envelope.protocol

            _LOGGER.info("Roteando mensagem de '%s' para protocolo '%s'", envelope.src, target_protocol)

            # Dispara o evento que os protocolos de SAÍDA estão ouvindo
            # Ex: send_to_mqtt, send_to_lora
            # os protocolos devem estar ouvindo "send_to_" + protocol_name

            event_topic = f"{EventState.SEND_TO.value}{target_protocol}"
            await event_bus.publish(event_topic, envelope)

        else:
            _LOGGER.warning("Recebeu um envelope inválido: %s")

