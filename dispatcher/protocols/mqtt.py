"""Protocolo MQTT para a Bifrost."""

import asyncio
import logging
from pathlib import Path

import aiomqtt
from pydantic import BaseModel, ValidationError

from ..core.event_bus import EventBus
from ..utils.device import Device
from ..utils.envelope import Envelope, parse_envelope
from ..utils.events import Events

_LOGGER = logging.getLogger(__name__)


class MqttConfig(BaseModel):
    host: str = "localhost"
    port: int = 1883
    username: str | None = None
    password: str | None = None


async def setup_protocol(config_dir: Path, raw_config: dict, event_bus: EventBus):
    """Setup do protocolo MQTT."""
    try:
        config = MqttConfig(**raw_config)
    except ValidationError as e:
        _LOGGER.error("Configuração MQTT inválida: %s", e)
        return

    async def mqtt_loop():
        """Loop principal de conexão e escuta MQTT."""
        async with aiomqtt.Client(
            hostname=config.host,
            port=config.port,
            username=config.username,
            password=config.password,
        ) as client:
            _LOGGER.info("Conectado ao Broker MQTT: %s", config.host)

            # --- SAÍDA: Escutar o EventBus para enviar ao MQTT ---
            async def handle_outbound(data: dict):
                envelope: Envelope | None = data.get("envelope")
                device: Device | None = data.get("device")

                if not envelope or not device:
                    _LOGGER.warning("Dados incompletos para roteamento: %s", data)
                    return

                # No MQTT, o destino está na config do dispositivo (tópico)
                topic = device.config.get("topic_out")

                if topic:
                    await client.publish(topic, envelope.model_dump_json())

            event_bus.subscribe(f"{Events.Protocol.SEND_PREFIX}mqtt", handle_outbound)

            # --- ENTRADA: Escutar tópicos do Broker ---
            # Aqui subscrevemos em um tópico genérico ou pegamos do banco futuramente
            await client.subscribe("bifrost/+/data")  # Ex: bifrost/sensor01/data

            async for message in client.messages:
                payload = message.payload.decode()
                envelope = parse_envelope(payload)
                if envelope:
                    await event_bus.publish(Events.Protocol.RECEIVED, envelope)

    # Inicia como uma task para não travar o start.py
    asyncio.create_task(mqtt_loop())
