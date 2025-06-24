import logging
import time

from config.settings import UART_PORTS, BAUD_RATE, MQTT_BROKER, MQTT_PORT, DEVICE_REGISTRY_PATH
from protocols import MQTTHandler, SerialHandler
from utils.envelope import make_envelope, serialize
from utils.registry import DeviceRegistry

# main()
# - Inicializa a comunicação com as unidades de cada protocolo e monitora recebimentos.
# - Se a mensagem recebida for válida, despacha para unidade de destino.
def main():
    print("Iniciando Dispatcher...")

    # Carrega o Registro de Dispositivos, com o protoclo e endereço/tópico de cada um.
    registry = DeviceRegistry(DEVICE_REGISTRY_PATH)
    
    # Instanciando o objeto de cada comunicação.
    #
    # - Comunicações do próprio Rasp devem ter sua própria Classe, como o MQTT.
    # - Comunicações via serial devem ser declaradas usando a Classe SerialHandler.
    handlers = {
        "MQTT": MQTTHandler(MQTT_BROKER, MQTT_PORT),
        "espnow": SerialHandler(UART_PORTS[2], BAUD_RATE),
    }

    print("Dispatcher Iniciado!")

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

        print("Encerrando.")
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
    #info = registry.get_by_address(source_address)

    #if info is None:
    #    request_for_register(source_address, source_handler)
    #    return

    # 3) Roteia mensagens válidas
    if destination_id == "central":
        print(f"[CENTRAL] {source_address} -> central:", message.get("payload"))
    
    # 4) Roteia Mensagens para outros dispositivos
    destination_info = registry.get_by_id(destination_id)

    if not destination_info:
        print(f"[DISPATCHER] Destino '{destination_id}' não cadastrado.")
        return

    destination_protocol = destination_info["protocol"]
    destination_handler  = handlers.get(destination_protocol)

    if destination_handler:
        message["dst"] = destination_info.get("adress") or destination_info.get("topic")
        destination_handler.handleMessage(destination_info=destination_info, message=message)
        print(f"[DISPATCHER] {source_address} → {destination_info} via {destination_protocol}")

    # 5) Mensagens ignoradas (descomentar para debugging)
    else:
        print(f"[DISPATCHER] Protocolo {destination_protocol} não implementado.")

# register_new_device()
#   - Recebe o dict da mensagem, o endereço do destinatário.
#   - Registra os dados no Registry
#   - Usa a comunicação de origem para enviar a resposta.
def register_new_device(message: dict, registry: DeviceRegistry, handlers):
    device_id       = message["payload"].get("id")
    source_address  = message.get("src")
    device_protocol = message.get("protocol")

    registry.add(device_id=device_id, address=source_address, protocol=device_protocol)

    # Enviando resposta para o dispositivo.
    response = make_envelope(
        src = "central",
        dst = source_address,
        msg_type = "register_response",
        payload = {"status":"registered", "id":device_id}
    )

    handlers[device_protocol].send(serialize(response))
    print(f"[REGISTRY] Novo dispositivo '{device_id}' @ {source_address}")

# request_for_register()
#   - Monta o JSON para requisitar os dados do dispositivo.
#   - Envia a requisição.
def request_for_register(source_address: str, source_handler):

    request = make_envelope(
        src = "central",
        dst = source_address,
        msg_type="register_request",
        payload={"status":"not_registered"}
    )

    source_handler.send(serialize(request))
    print(f"[DISPATCHER] {source_address} não cadastrado, solicitação de registro enviada.")
    return

if __name__ == "__main__":
    main()
