"""Roteador de Mensagem. Lê as mudanças de estado e direciona as mensagens para seu destino correto."""

import logging

from core.event_bus import event_bus
from core.events import Events
from utils.envelope import Envelope


_LOGGER = logging.getLogger(__name__)


class Router:
        _LOGGER.info("Iniciando Router de Mensagens.")


        # O Router só ouve mensagens que já foram aprovadas pelo Registry
        event_bus.subscribe(Events.Device.VALIDATED, self.route_message)

        _LOGGER.info("Sucesso ao iniciar o Router!")
    async def route_message(self, data: dict):
        """Recebe um dicionário contendo o envelope e os dados do dispositivo."""

        envelope: Envelope | None = data.get("envelope")

        if envelope:
            target_protocol = envelope.protocol

            _LOGGER.info("Roteando mensagem de '%s' para protocolo '%s'", envelope.src, target_protocol)

            # Dispara o evento que os protocolos de SAÍDA estão ouvindo
            # Ex: send_to_mqtt, send_to_lora
            # os protocolos devem estar ouvindo "send_to_" + protocol_name

            event_topic = f"{Events.Protocol.SEND_PREFIX}{target_protocol}"
            await event_bus.publish(event_topic, envelope)

        else:
            _LOGGER.warning("Recebeu um envelope inválido: %s")

