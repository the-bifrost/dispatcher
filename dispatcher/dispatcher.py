"""Lógica de Roteamento de Mensagens."""

import asyncio
import logging


from dispatcher.models.devices import Device, EspNowDevice, MqttDevice, LoraDevice
from dispatcher.utils.device_factory import create_device
from dispatcher.utils.envelope import Envelope
from dispatcher.services.registry import DeviceRegistry
from dispatcher.services.database import write_data, envelope_to_point_dict

_LOGGER = logging.getLogger(__name__)

class Dispatcher:
    """Gerencia o roteamento de mensagens entre dispositivos."""

    def __init__(self, registry: DeviceRegistry, handlers: dict):
        self._registry = registry
        self._handlers = handlers

    async def dispatch(self, message: Envelope):
        """Recebe um envelope válido e despacha de forma assíncrona."""

        # 1. Requisições de Registro
        if message.dst == "central" and message.type == "register":
            await self._handle_registration(message)
            return
        
        # 2. Verifica se o remetente é conhecido
        source_devices = self._registry.search(message.src)
        if not source_devices:
            await self._request_registration(message)
            return
        
        source_device = source_devices[0]

        # 3. Roteia a mensagem
        if message.dst == "central":
            _LOGGER.info("[CENTRAL] %s -> central: %s", message.src, message.payload)

            point = envelope_to_point_dict(message=message, measurement=message.type)
            await asyncio.to_thread(write_data, point)
        else:
            await self._route_to_device(message, source_device)

    # Envia requisições de registro
    async def _handle_registration(self, message: Envelope):
        """Registra um novo dispositivo e envia resposta de confirmação."""

        device_id = message.payload.get("id")
        device_type = message.payload.get("device_type")

        if not device_id or not device_type:
            _LOGGER.warning("Tentativa de registro inválida. ID: %s | Device_Type: %s", device_id, device_type)
            return
        
        handler = self._handlers.get(message.protocol)

        if not handler:
            _LOGGER.error("Handler para o protocolo '%s' não encontrado para registro.", message.protocol)
            return
        
        device_data = {
            "protocol": message.protocol,
            "device_type": device_type,
            **message.payload
        }

        # 1. Pergunta ao handler qual é o campo de endereço dele.
        address_key = handler.address_field
        # 2. Se o handler tiver um campo de endereço, usa o 'src' da mensagem.
        if address_key:
            device_data[address_key] = message.src

        device_object = create_device(device_data)

        if not device_object:
            _LOGGER.error(f"Factory falhou ao criar dispositivo para dados: {device_data}")
            return
        
        is_new = self._registry.add(device_id=device_id, device_data=device_object)
        
        response = Envelope(
            v=1, protocol=message.protocol, src="central", dst=message.src,
            type="register_response",
            payload={"status": "success" if is_new else "already_registered", "device_id": device_id}
        )
        
        await handler.write(response, device_object)
        _LOGGER.debug(f"{message.src} cadastrado com sucesso.")


    async def _request_registration(self, message: Envelope):
        """Solicita que um dispositivo desconhecido se registre."""
        handler = self._handlers.get(message.protocol)
        if not handler:
            _LOGGER.error(f"Handler para protocolo '{message.protocol}' não encontrado.")
            return

        # A mesma lógica dinâmica se aplica aqui.
        temp_data = {"protocol": message.protocol, "device_type": "unknown"}
        
        address_key = handler.address_field
        if address_key:
            temp_data[address_key] = message.src

        temp_device = create_device(temp_data)
        if not temp_device:
            _LOGGER.error(f"Factory falhou ao criar device temporário para {message.src}")
            return
        
        request = Envelope(
            v=1, protocol=message.protocol, src="central", dst=message.src,
            type="register_request", payload={"status": "not_registered"}
        )
        await handler.write(request, temp_device)
        _LOGGER.debug(f"{message.src} não cadastrado, solicitação de registro enviada.")

    async def _route_to_device(self, message: Envelope, source_device: Device):
        """Roteia uma mensagem de um dispositivo conhecido para outro."""
        destination_info = self._registry.get_by_id(message.dst)
        if not destination_info:
            _LOGGER.debug(f"[DISPATCHER] Destino '{message.dst}' não cadastrado.")
            return
        
        dest_handler = self._handlers.get(destination_info.protocol)
        if not dest_handler:
            _LOGGER.debug(f"[DISPATCHAER] Protocolo '{destination_info.protocol}' não implementado.")
            return
        
        send_success = await dest_handler.write(message, destination_info)
        
        if send_success:
            _LOGGER.info(f"[DISPATCHER] '{message.src}' ({source_device.device_type}) → '{message.dst}' via '{destination_info.protocol}'")
            point = envelope_to_point_dict(message=message, measurement=source_device.device_type)
            await asyncio.to_thread(write_data, point)

