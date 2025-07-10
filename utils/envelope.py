""" Envelopamento e Desenvelopamento de Mensagens.

Esse módulo é uma coletânea de funções para envelopar/desenvelopar/encriptar dados
que são lidos pela Bifrost.

Exemplos de uso:

    received_message = deserialize(received_data)
    message = make_envelope(source_id, "central", {"response":"ok"})
    message_serialized = serialize(message)
"""

import json
import logging
import time

logger = logging.getLogger(__name__)

def make_envelope(src: str, dst: str, payload, msg_type="state", version=1) -> dict:
    """Monta uma mensagem no padrão Bifrost de acordo com os dados recebidos.

    Args:
        src: Remetente da mensagem.
        dst: Destinatário da mensagem.
        payload: Pode ser qualquer tipo de dado, preferencialmente um dicionário.
        msg_type: O assunto da mensagem.
        version: versionamento da mensagem, para evitar quebrar o código no futuro.
    """
    return {
        "v": version,
        "src": src,
        "dst": dst,
        "type": msg_type,
        "ts": int(time.time()),
        "payload": payload
    }

def serialize(data: dict) -> str:
    """Converte um dicionário em uma string JSON

    Args:
        data: Um dicionário que será convertido em JSON.

    Returns:
        Uma string JSON em caso de sucesso:

        {"protocol": "MQTT", "topic": "/example/state"}
         
        Caso ocorrer algum erro durante a conversão, retorna um JSON vazio:

        {}
    """
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logger.error("Erro ao serializar o dicionário: %s", e)

def deserialize(data_string: str) -> dict | None:
    """Converte uma string JSON em um dicionário de informações.
    
    Args:
        data_string: Uma string JSON com dados de um dispositivo.
    
    Returns:
        Um dicionário em caso de sucesso:

        {
            "protocol": "MQTT", 
            "topic": "/example/state"
        }
         
        Caso ocorrer algum erro durante a conversão, retorna um None.
    """
    try:
        return json.loads(data_string)
    except json.JSONDecodeError as e:
        logger.error("Erro ao converter string em dicionário: %s", e)
        return None
    except Exception as e:
        logger.error("Erro inesperado: %s", e)
        return None