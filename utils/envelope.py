"""Gerenciamento dos Envelopes da Bifrost."""

import json
import logging
import time
from typing import Any, Dict

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class Envelope(BaseModel):
    """Envelope padrão para mensagens da Bifrost"""
    v: int
    protocol: str
    src: str
    dst: str
    type: str
    ts: int
    payload: Dict[str, Any] = {}


def parse_envelope(message: str) -> Envelope | None:
    """Tenta converter strings em Envelope."""
    try:
        return Envelope.model_validate_json(message)
    except ValidationError as e:
        logger.info("Mensagem com formato inválido: %s", e)
        return None


##########################################################################################
#                          Implementação antiga da biblioteca                            #
##########################################################################################

def make_envelope(src: str, dst: str, payload, msg_type="state", version=1) -> dict:
    """Monta uma mensagem no padrão Bifrost de acordo com os dados recebidos."""
    return {
        "v": version,
        "src": src,
        "dst": dst,
        "type": msg_type,
        "ts": int(time.time()),
        "payload": payload
    }

def serialize(data: dict) -> str:
    """Converte um dicionário em uma string JSON"""
    try:
        return json.dumps(data)
    except (TypeError, ValueError) as e:
        logger.error("Erro ao serializar o dicionário: %s", e)


def deserialize(data_string: str) -> dict | None:
    """Converte uma string JSON em um dicionário de informações."""
    try:
        return json.loads(data_string)
    except json.JSONDecodeError as e:
        logger.error("Erro ao converter string em dicionário: %s", e)
        return None
    except Exception as e:
        logger.error("Erro inesperado: %s", e)
        return None