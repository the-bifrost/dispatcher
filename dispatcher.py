"""Confere e despacha as mensagens."""

import logging
from utils.envelope import Envelope

logger = logging.getLogger(__name__)

def dispatch(message: dict, registry, handlers: dict):
    """Despacha mensagens válidas para seus destinatários"""
    logger.debug("Recebido a mensagem: %s", message)

    if response_message := validate_message(message, handlers) is not None:
        handlers


    pass





def validate_message(message: dict, registry):
    """Recebe e valida mensagens, retorna a resposta"""

    if is_register_request():
        register_new_device(message=message, registry=registry, handlers=handlers)
        return

    if not is_known_device(message, registry):
        source_handler = message.get("protocol")
        request_for_register(message.get("address"), handlers.get(source_handler))
        return

    return None
    

def is_register_request(message) -> bool:
    return message.get("dst") == "central" and message.get("type") == "register"

def is_known_device(message, registry) -> bool:
    return registry.get_by_address(message.get("src")) is not None

    
    # 3) Roteia mensagens válidas
    if destination_id == "central":
        logger.info("[CENTRAL] %s -> central: %s", source_address, message.get("payload"))
    
    # 4) Roteia Mensagens para outros dispositivos
    destination_info = registry.get_by_id(destination_id)

    if not destination_info:
        logger.debug("[DISPATCHER] Destino '%s' não cadastrado", destination_id)
        return

    destination_protocol = destination_info["protocol"]
    destination_handler  = handlers.get(destination_protocol)

    if destination_handler:
        message["dst"] = destination_info.get("adress") or destination_info.get("topic")
        destination_handler.handleMessage(destination_info=destination_info, message=message)
        logger.info("[DISPATCHER] '%s' → '%s' via '%s'", source_address, destination_info, destination_protocol)


# register_new_device()
#   - Recebe o dict da mensagem, o endereço do destinatário.
#   - Registra os dados no Registry
#   - Usa a comunicação de origem para enviar a resposta.
def register_new_device(message: dict, registry, handlers):
    device_id       = message["payload"].get("id")
    source_address  = message.get("src")
    device_protocol = message.get("protocol")

    response = registry.add(device_id=device_id, address=source_address, protocol=device_protocol)
    handlers[device_protocol].send(serialize(response))


# request_for_register()
#   - Monta o JSON para requisitar os dados do dispositivo.
#   - Envia a requisição.
def request_for_register(source_address: str, handler) -> bool:

    if not handler:
        logger.error("request_for_register() -> HANDLER tem valor nulo")
        return False

    request = make_envelope(
        src = "central",
        dst = source_address,
        msg_type="register_request",
        payload={"status":"not_registered"}
    )

    handler.send(serialize(request))
    logger.debug("[DISPATCHER] %s não cadastrado, solicitação de registro enviada.", source_address)
    return True