"""Handler para comunicação MQTT utilizando a lib asyncio-mqtt."""

import asyncio
import logging

import aiomqtt as mqtt

from .base_handler import BaseHandler
from dispatcher.models.devices import Device, MqttDevice
from dispatcher.utils.envelope import Envelope, parse_envelope

_LOGGER = logging.getLogger(__name__)


class MqttHandler(BaseHandler):
    """Implementa a comunação MQTT de forma assíncrona no padrão Handler Bifrost."""

    def __init__(self, broker: str, port: int = 1883):
        self._broker = broker
        self._port = port
        self._inbox = asyncio.Queue()

        self._client = mqtt.Client(hostname=self._broker, port=self._port)
        self._listener_task: asyncio.Task | None = None
        self._subscribed_topics: set[str] = set()

    @property
    def protocol(self) -> str:
        return "mqtt"
    
    @property
    def address_field(self) -> str:
        return "topic_out"

    async def start(self):
        """Conecta ao broker e inicia a tarefa de escuta de mensagens."""

        try:
            await self._client.__aenter__()
            _LOGGER.info("Conecado ao broker MQTT em %s:%d", self._broker, self._port)

            # Reinscreve em tópicos
            for topic in self._subscribed_topics:
                await self._client.subscribe(topic)
                
                # Inicia tarefa em background para ouvir mensanges
                self._listener_task = asyncio.create_task(self._listen())
        except Exception as e:
            _LOGGER.error("Falha ao conectar ou iniciar o listener MQTT: %s", e)
            raise

    async def _listen(self):
        """Tarefa de longa duração que ouve mensagens e coloca na fila."""

        _LOGGER.info("Listener MQTT iniciado. Aguardando mensagens...")

        try:
            async for message in self._client.messages:

                try:
                    payload = message.payload

                    if isinstance(payload,bytes):
                        payload_str = payload.decode('utf-8')
                    else:
                        payload_str = str(payload)

                    envelope = parse_envelope(payload_str)

                    if envelope:
                        self._inbox.put_nowait(envelope)
                    else:
                        _LOGGER.warning("Mensagem inválida no tópico '%s': %s", message.topic, payload_str)
                except Exception as e:
                        _LOGGER.error("Erro ao processar mensagem do tópico '%s': %s", message.topic, e)
        except asyncio.CancelledError:
            _LOGGER.info("Listener MQTT cancelado.")
        except Exception as e:
            _LOGGER.error("Erro crítico no listener MQTT: %s", e, exc_info=True)


    async def read(self) -> Envelope | None:
        """Pega a próxima mensagem da fila interna de forma assíncrona."""
        return await self._inbox.get()

    async def write(self, envelope: Envelope, device: Device) -> bool:
        """Publica um envelope para o tópico de destino do dispositivo."""
        if not isinstance(device, MqttDevice):
            _LOGGER.error("Tipo de dispositivo incorreto. Esperado: MqttDevice, Recebido: %s", type(device).__name__)
            return False

        topic = device.destination
        json_payload = envelope.model_dump_json()

        try:
            await self._client.publish(topic, payload=json_payload, qos=1)
            _LOGGER.info("Publicado em '%s': '%s'", topic, json_payload)
            return True
        except Exception as e:
            _LOGGER.error("Falha ao publicar no tópico '%s': %s", topic, e)
            return False

    async def subscribe(self, topic: str):
        """Inscreve-se em um tópico dinamicamente."""
        self._subscribed_topics.add(topic)
        
        # Se o cliente já estiver conectado, inscreve-se imediatamente
        if self._client._connected.done():
            try:
                await self._client.subscribe(topic)
                _LOGGER.info("Inscrito no tópico: '%s'", topic)
            except Exception as e:
                _LOGGER.error("Falha ao se inscrever no tópico '%s': %s", topic, e)

    async def close(self):
        """Cancela a tarefa de escuta e agenda a desconexão."""
        _LOGGER.info("Fechando conexão MQTT...")
        if self._listener_task:
            self._listener_task.cancel()
            
        if self._client._connected.done():
            await self._client.__aexit__(None, None, None)

