"""Confere e despacha as mensagens."""

import logging

from models.devices import Device, EspNowDevice, MqttDevice
from utils.envelope import Envelope
from utils.registry import DeviceRegistry
from utils.database import write_data, envelope_to_point_dict, close_write_api

logger = logging.getLogger(__name__)

class Dispatcher:
    """Gerencia o roteamento de mensagens entre dispositivos."""

    def __init__(self, registry: DeviceRegistry, handlers: dict):
        self._registry = registry
        self._handlers = handlers


    def dispatch(self, message: Envelope):
        """Recebe um envelope válido e dispara conforme necessário."""

        # 1. Requisições de Registro
        if self._is_register_request(message):
            self._handle_registration(message)
            return
        
        # 2. Verifica se o remetente é conhecido
        source_devices = self._registry.search(address=message.src)

        if not source_devices:
            self._request_registration(message)
            return
        
        # Pega o primeiro dispositivo da lista
        source_device = source_devices[0]
        
        # 3. Roteia a mensagem para a central
        if message.src == "central":
            logger.info(f"[CENTRAL] {message.src} -> central: {message.payload}")
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
            logger.warning("Tentativa de registro sem 'id' no payload")
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
                topic=message.src
            )

        if not device_object:
            logger.error(f"Protocolo de registro desconhecido: {message.protocol}")
            return
        
        response_payload = self._registry.add(
            device_id=device_id,
            device_data=device_object
        )
        
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
            handler.send(response)
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
        
        request = Envelope(
            v=1,
            protocol=message.protocol,
            src="central",
            dst=message.src,
            type="register_request",
            payload={"status":"not_registered"}
        )

        handler.send(request)
        logger.debug(f"{message.src} não cadastrado, solicitação de registro enviada.")


    def _route_to_device(self, message: Envelope, source_info: Device):
        """Roteia uma mensagem de um dispositivo conhecido para outro."""

        destination_info = self._registry.get_by_id(message.dst)

        if not destination_info:
            logger.debug(f"[DISPATCHER] Destino '{message.dst}' não cadastrado.")
            return
        
        dest_protocol = destination_info.get("protocol")
        dest_handler = self._handlers.get(dest_protocol)

        if not dest_handler:
            logger.debug(f"[DISPATCHER] Protocolo '{dest_protocol}' não implementado.")
            return
        
        envelope = Envelope(
            v = 1,
            protocol = dest_protocol,
            src = message.src,
            dst = destination_info.get("address"),
            payload=message.payload
        )
        dest_handler.send(envelope)
        
        logger.info(f"[DISPATCHER] '{message.src}' → '{destination_info}' via '{dest_protocol}'")

        # Escreve os dados no banco de dados
        point = envelope_to_point_dict(message=envelope, measurement=source_info.get("device_type"))
        write_data(point)