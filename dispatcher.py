import json
import logging
import logging.config
import time

from pathlib import Path

from protocols import MQTTHandler, SerialHandler
from utils.config_loader import load_config
from utils.envelope import make_envelope, serialize
from utils.registry import DeviceRegistry

cfg = load_config("config/config.toml")

logger = logging.getLogger()

def setup_logging():
    logger_config = load_config(cfg.paths.logger_config)
    logging.config.dictConfig(logger_config)

# main()
# - Inicializa a comunicação com as unidades de cada protocolo e monitora recebimentos.
# - Se a mensagem recebida for válida, despacha para unidade de destino.
def main():
    setup_logging()

    logger.info("Iniciando Dispatcher...")

    # Carrega o Registro de Dispositivos, com o protoclo e endereço/tópico de cada um.
    registry = DeviceRegistry(Path(__file__).parent / cfg.paths.device_registry)
    
    # Instanciando o objeto de cada comunicação.
    #
    # - Comunicações do próprio Rasp devem ter sua própria Classe, como o MQTT.
    # - Comunicações via serial devem ser declaradas usando a Classe SerialHandler.
    handlers = {
        "MQTT": MQTTHandler(cfg.mqtt.broker, cfg.mqtt.port),
        "espnow": SerialHandler(cfg.uart.ports[2], cfg.uart.baudrate),
    }

    logger.info("Dispatcher Iniciado!")

    # Faz a leitura contínua de todos os protocolos configurados.
    #  - Sempre que receber uma mensagem, envia para o dispatcher.
    try:
        while True:
            for handler in handlers.values():
                message = handler.read()
                if (message):
                    dispatch(message, registry, handlers)
            time.sleep(0.1)
    
    # Encerra o programa
    except KeyboardInterrupt:
        for handler in handlers.values():
            handler.close()

        logger.info("Encerrando Dispatcher...")        
        exit(1)

# dispatch()
#   - Salva o endereço do remetente, o ID do destinatário e o tipo de mensagem.
#   - Confere se a mensagem recebida tem um destinatário válido.
#   - Confere se esse destinatário possui um protocolo cadastrado.
#   - Envia de acordo com protocolo e destino.
#   - A validação dos campos PRECISA ACONTECER EM GET().
def dispatch(message: dict, registry: DeviceRegistry, handlers: dict):

    message_type   = message.get("type")
    destination_id = message.get("dst")
    source_address = message.get("src")
    
    # 1) Se for um dispositivo pedindo para se registrar
    if destination_id == "central" and message_type == "register":
        register_new_device(message=message, registry=registry, handlers=handlers)
        return

    # 2) Se o remetente é desconhecido, pede para se registrar
    info = registry.get_by_address(source_address)

    if info is None:
        source_handler = message.get("protocol")
        request_for_register(source_address, handlers[source_handler])
        return

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

    # 5) Mensagens ignoradas (descomentar para debugging)
    else:
        logger.debug("[DISPATCHER] Protocolo %s não implementado.", destination_protocol)

# register_new_device()
#   - Recebe o dict da mensagem, o endereço do destinatário.
#   - Registra os dados no Registry
#   - Usa a comunicação de origem para enviar a resposta.
def register_new_device(message: dict, registry: DeviceRegistry, handlers):
    device_id       = message["payload"].get("id")
    source_address  = message.get("src")
    device_protocol = message.get("protocol")

    response = registry.add(device_id=device_id, address=source_address, protocol=device_protocol)
    handlers[device_protocol].send(serialize(response))


# request_for_register()
#   - Monta o JSON para requisitar os dados do dispositivo.
#   - Envia a requisição.
def request_for_register(source_address: str, handler):

    request = make_envelope(
        src = "central",
        dst = source_address,
        msg_type="register_request",
        payload={"status":"not_registered"}
    )

    handler.send(serialize(request))
    logger.debug("[DISPATCHER] %s não cadastrado, solicitação de registro enviada.", source_address)
    return

if __name__ == "__main__":
    main()
