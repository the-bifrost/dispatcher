"""Tipos de nó disponíveis no Flow Engine da Bifrost."""

import logging

from ..core.event_bus import event_bus
from ..utils.events import Events
from .node import Node


_LOGGER = logging.getLogger(__name__)


def _get_field(data: dict, path: str):
    """Lê um campo de um dicionário usando notação de ponto (ex: 'sensor.temp')."""
    value = data

    for part in path.split("."):
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return None

    return value


class InputNode(Node):
    """Ponto de entrada do flow. Escuta mensagens validadas de um dispositivo específico."""

    async def on_event(self, data: dict):
        """Callback inscrito no EventBus para Device.VALIDATED."""
        envelope = data.get("envelope")

        if not envelope:
            return

        device_id = self.config.get("device_id")

        if device_id and envelope.src != device_id:
            return

        await self.receive(data)

    async def process(self, message: dict) -> dict | None:
        return message


class OutputNode(Node):
    """Ponto de saída do flow. Envia a mensagem para o protocolo do dispositivo destino."""

    async def process(self, message: dict) -> dict | None:
        device_id = self.config.get("device_id")
        envelope = message.get("envelope")

        if not device_id or not envelope:
            _LOGGER.warning("OutputNode %s sem device_id/envelope configurado", self.id)
            return None

        device = await self.registry.get_device(device_id)

        if not device:
            _LOGGER.warning("OutputNode %s: dispositivo destino '%s' não encontrado", self.id, device_id)
            return None

        event_topic = f"{Events.Protocol.SEND_PREFIX}{device.protocol}"
        await event_bus.publish(event_topic, {"envelope": envelope, "device": device})

        return None


class FilterNode(Node):
    """Deixa a mensagem passar somente se a condição configurada for verdadeira."""

    OPERATORS = {
        "eq": lambda a, b: a == b,
        "neq": lambda a, b: a != b,
        "gt": lambda a, b: a > b,
        "gte": lambda a, b: a >= b,
        "lt": lambda a, b: a < b,
        "lte": lambda a, b: a <= b,
    }

    async def process(self, message: dict) -> dict | None:
        envelope = message.get("envelope")

        if not envelope:
            return None

        field = self.config.get("field", "")
        op = self.config.get("op", "eq")
        expected = self.config.get("value")

        actual = _get_field(envelope.payload, field)
        operator = self.OPERATORS.get(op)

        if actual is None or operator is None:
            return None

        try:
            if operator(actual, expected):
                return message
        except TypeError:
            _LOGGER.debug("FilterNode %s: comparação inválida entre %r e %r", self.id, actual, expected)

        return None


class TransformNode(Node):
    """Modifica o payload da mensagem antes de repassá-la."""

    async def process(self, message: dict) -> dict | None:
        envelope = message.get("envelope")

        if not envelope:
            return None

        new_payload = dict(envelope.payload)

        for key, value in self.config.get("set", {}).items():
            if isinstance(value, str) and value.startswith("$"):
                new_payload[key] = _get_field(envelope.payload, value[1:])
            else:
                new_payload[key] = value

        new_envelope = envelope.model_copy(update={"payload": new_payload})

        return {**message, "envelope": new_envelope}


class DebugNode(Node):
    """Loga a mensagem que passa por ele, sem modificá-la."""

    async def process(self, message: dict) -> dict | None:
        envelope = message.get("envelope")
        _LOGGER.info("[DEBUG %s] %s", self.id, envelope.model_dump_json() if envelope else message)
        return message


NODE_REGISTRY: dict[str, type[Node]] = {
    "input": InputNode,
    "output": OutputNode,
    "filter": FilterNode,
    "transform": TransformNode,
    "debug": DebugNode,
}
