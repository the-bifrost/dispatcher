"""Handler para enviar e receber dados MQTT."""

import time
import logging
import json
from queue import Queue, Empty
from typing import List

import paho.mqtt.client as mqtt
from paho.mqtt.client import MQTTMessage

from protocols import BaseHandler
from models.devices import Device, MqttDevice
from utils.envelope import Envelope

logger = logging.getLogger(__name__)

class MqttConnectionError(Exception):
    """Exceção para falhas de conexão com o Broker MQTT."""
    pass


class MqttHandler(BaseHandler):
    """Handler para comunicação MQTT usando uma fila interna (inbox)."""
    
    def __init__(self, broker: str, port: int = 1883):
        self._broker = broker
        self._port = port

        # Usamos a lib queue para criar um inbox de mensagens.
        self._inbox: Queue[Envelope] = Queue()
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        self._is_connected = False
        self._topics: set[str] = set()

        # Declarando as funções assíncronas da paho mqtt
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message
        self._client.on_disconnect = self._on_disconnect

    def start(self):
        """Inicia a conexão com o broker e se inscreve nos tópicos fornecidos."""
        logger.info("Conectando a %s:%s...", self._broker, self._port)

        try:
            self._client.connect(self._broker, self._port, 60)
            self._client.loop_start()
        except Exception as e:
            raise MqttConnectionError(f"Falha na conexão inicial com {self._broker}:{self._port}: {e}") from e
        
    def subscribe(self, topic: str):
        """Se inscreve em um novo tópico dinamicamente."""
        if topic not in self._topics:
            self._topics.add(topic)
             
            if self._is_connected:
                self._client.subscribe(topic)
                logger.info("Inscrito dinamicamente no tópico: '%s'", topic)

    def unsubscribe(self, topic: str):
        """Cancela a inscrição em um tópico dinamicamente."""
        if topic in self._topics:
            self._topics.remove(topic)
            if self._is_connected:
                self._client.unsubscribe(topic)
                logger.info("Inscrição cancelada para o tópico: '%s'", topic)

        # --- Implementação da Interface BaseHandler ---

    def read(self) -> Envelope | None:
        """Pega a próxima mensagem da fila (inbox) de forma não bloqueante."""

        try:
            return self._inbox.get_nowait()
        except Empty:
            return None
        
    def write(self, envelope: Envelope, device: Device):
        """Publica um envelope para o tópico associado ao dispositivo."""

        if not isinstance(device, MqttDevice):
            logger.error("Tentativa de escrita para um dispositivo não-MQTT. Dispositivo: %s", device.device_type)
            return None
            
        if not self._is_connected:
            logger.warning("Não foi possível publicar, cliente MQTT não conectado.")
            return None
            
        try:
            topic = device.topic
            json_payload = envelope.model_dump_json()

            info = self._client.publish(topic, json_payload, qos=1)

            if info.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug("Envelope publicado com sucesso no tópico '%s'", topic)
                return
            else:
                logger.warning("Falha ao publicar no tópico '%s'. Código: %s", topic, info.rc)
                return None
        except Exception as e:
            logger.error("Erro inesperado durante a publicação MQTT: %s", e)
            return None
            
    def close(self):
        """Encerra a thread de rede e desconecta do broker."""
        logger.info("Fechando conexão MQTT...")
        self._client.loop_stop()
        self._client.disconnect()

    # --- Callbacks Internos do Paho MQTT ---


    def _on_connect(self, client, userdata, flags, rc):
        """Callback executado ao conectar (ou reconectar)."""

        if rc == 0:
            self._is_connected = True
            logger.info("Conectado ao Broker MQTT com sucesso!")

            for topic in self._topics:
                client.subscribe(topic)
                logger.info("Inscrito no tópico: '%s'", topic)
        else:
            self._is_connected = False
            logger.error("Falha na conexão com o Broker. Código de retorno: %s", rc)
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback executado ao desconectar."""
        self._is_connected = False
        logger.warning("Desconectado do Broker MQTT. Código: %s", rc)

    def _on_message(self, client, userdata, msg: MQTTMessage):
        """Callback executado ao receber uma mensagem."""
        try:
            payload_str = msg.payload.decode('utf-8')
            envelope = Envelope.model_validate_json(payload_str)
            
            # Coloca o envelope processado na fila para o `read()` pegar
            self._inbox.put(envelope)
            
            logger.debug("Envelope do tópico '%s' adicionado à fila.", msg.topic)
        except json.JSONDecodeError:
            logger.warning("Recebida mensagem não-JSON no tópico '%s'. Ignorando.", msg.topic)
        except Exception as e:
            logger.error("Erro ao processar mensagem do tópico '%s': %s", msg.topic, e)
