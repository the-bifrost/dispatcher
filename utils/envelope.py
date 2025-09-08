"""Gerenciamento dos Envelopes da Bifrost."""

import json
import logging
import time
from typing import Any, Dict, Literal

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class Envelope(BaseModel):
    """Envelope padrão para mensagens da Bifrost"""
    v: int
    protocol: str
    src: str
    dst: str
    type: str
    ts: int = int(time.time())
    payload: Dict[str, Any] = {}


def parse_envelope(message: str) -> Envelope | None:
    """Tenta converter strings em Envelope."""
    try:
        return Envelope.model_validate_json(message)
    except ValidationError as e:
        logger.info("Mensagem com formato inválido: %s", e)
        return None
