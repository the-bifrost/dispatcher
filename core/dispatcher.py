"""Confere e despacha as mensagens."""

import logging

from models.devices import Device, EspNowDevice, MqttDevice, LoraDevice
from utils.device_factory import create_device
from utils.envelope import Envelope
from services.registry import DeviceRegistry
from services.database import write_data, envelope_to_point_dict

logger = logging.getLogger(__name__)

class Dispatcher:
    """Gerencia o roteamento de mensagens entre dispositivos."""

    def __init__(self, registry: DeviceRegistry, handlers: dict):
        self._registry = registry
        self._handlers = handlers

        # Inscrição inicial em tópicos já cadastrados
        mqtt_handler  = self._handlers.get("mqtt")

        if mqtt_handler:
            initial_topics = self._registry.get_mqtt_topics()

            for topic in initial_topics:
                mqtt_handler.subscribe(topic)

            logger.info("Sincronização inicial: %d tópicos MQTT inscritos.", len(initial_topics))


    def dispatch(self, message: Envelope):
        """Recebe um envelope válido e dispara conforme necessário."""

        # Atenção!
        # Desconmentar essa linha apenas para debbug do código.
        #logger.debug("Mensagem recebida: %s", message)

        # 1. Requisições de Registro
        if self._is_register_request(message):
            self._handle_registration(message)
            return
        
        # 2. Verifica se o remetente é conhecido
        source_devices = self._registry.search(message.src)

        logger.debug(source_devices)

        if not source_devices:
            self._request_registration(message)
            return
        
        # Pega o primeiro dispositivo da lista
        source_device = source_devices[0]
        
        # 3. Roteia a mensagem para a central
        if message.dst == "central":
            logger.info(f"[CENTRAL] {message.src} -> central: {message.payload}")

            point = envelope_to_point_dict(message=message, measurement=message.type)
            write_data(point)
        else:
            self._route_to_device(message, source_device)


    ##########################################################################################
    #                                Funções de Registro                                     #
    ##########################################################################################

    def _is_register_request(self, message: Envelope):
        """Valida requisições de cadastramento."""
        return message.dst == "central" and message.type == "register"


    def _handle_registration(self, message: Envelope):
        """Registra um novo dispositivo e envia uma resposta de confirmação"""
        device_id = message.payload.get("id")
        device_type = message.payload.get("device_type")

        if not device_id or not device_type:
            logger.warning("Tentativa de registro inválida. ID: %s | Device_Type: %s", device_id, device_type)
            return
        
        device_object: Device | None = None

        if message.protocol == "espnow":
            device_object = EspNowDevice(
                protocol="espnow",
                device_type=device_type,
                address=message.src
            )
        elif message.protocol == "mqtt":
            device_object = MqttDevice(
                protocol="mqtt",
                device_type=device_type,
                topic_in=message.payload["topic_in"],
                topic_out=message.payload["topic_out"]
            )
        elif message.protocol == "lora":
            device_object = LoraDevice(
                protocol="lora",
                device_type=device_type,
                device_id=message.src
            )
        if not device_object:
            logger.error(f"Protocolo de registro desconhecido: {message.protocol}")
            return
        
        is_new = self._registry.add(device_id=device_id, device_data=device_object)
        

        if is_new and isinstance(device_object, MqttDevice):
            mqtt_handler = self._handlers.get("mqtt")
            if mqtt_handler:
                logger.info("Novo dispositivo MQTT registrado. Atualizando inscrição para o tópico: %s", device_object.topic_out)
                mqtt_handler.subscribe(device_object.topic_out)

        if is_new:
            response_payload = { "status": "success", "device_id": device_id }
        else:
            response_payload = { "status": "already_registered", "device_id": device_id }
        
        response = Envelope(
            v = 1,
            protocol = message.protocol,
            src = "central",
            dst = message.src,
            type = "register_response",
            payload = response_payload
        )

        handler = self._handlers.get(message.protocol)

        if handler:
            handler.write(response, device_object)
            logger.debug(f"{message.src} cadastrado com sucesso.")
        else:
            logger.error("Handler para o protocolo '%s' não encontrado para enviar resposta de registro.", message.protocol)
            return


    def _request_registration(self, message: Envelope):
        """Solicita que um dispositivo conhecido se registre."""

        handler = self._handlers.get(message.protocol)

        if not handler:
            logger.error(f"Handler para protocolo '{message.protocol}' não encontrado para solicitar registro.")
            return
        
        # Montando um dicionário com dados temporários do dispositivo
        device_data = {
            "protocol": message.protocol,
            "device_type": "unknown"  # O tipo é desconhecido nesta fase, o que é ok
        }
        if message.protocol == "espnow":
            device_data["address"] = message.src
        elif message.protocol == "mqtt":
            device_data["topic"] = message.src
        else:
            logger.error(f"Protocolo '{message.protocol}' não tem lógica para criar device temporário.")
            return

        # 2. Usa a factory para criar o objeto Device temporário
        temp_device = create_device(device_data)

        # 3. Garante que o objeto foi criado com sucesso
        if not temp_device:
            logger.error(f"Factory falhou ao criar device temporário para dados: {device_data}")
            return
        
        request = Envelope(
            v=1,
            protocol=message.protocol,
            src="central",
            dst=message.src,
            type="register_request",
            payload={"status":"not_registered"}
        )

        handler.write(request, temp_device)
        logger.debug(f"{message.src} não cadastrado, solicitação de registro enviada.")


    def _route_to_device(self, message: Envelope, source_info: Device):
        """Roteia uma mensagem de um dispositivo conhecido para outro."""

        destination_info = self._registry.get_by_id(message.dst)

        if not destination_info:
            logger.debug(f"[DISPATCHER] Destino '{message.dst}' não cadastrado.")
            return
        
        dest_protocol = destination_info.protocol
        dest_handler = self._handlers.get(dest_protocol)

        if not dest_handler:
            logger.debug(f"[DISPATCHER] Protocolo '{dest_protocol}' não implementado.")
            return
        
        envelope_to_send = Envelope(
            v = 1,
            protocol = message.protocol,  
            src = message.src,
            dst = message.dst,
            type = message.type,
            payload = message.payload
        )
        
        send_success = dest_handler.write(envelope_to_send, destination_info)
        
        logger.info(f"[DISPATCHER] '{message.src}' → '{destination_info}' via '{dest_protocol}'")

        # Escreve os dados no banco de dados
        if send_success:
            point = envelope_to_point_dict(message=envelope_to_send, measurement=source_info.device_type)
            write_data(point)