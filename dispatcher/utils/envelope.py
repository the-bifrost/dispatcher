"""Gerenciamento dos Envelopes da Bifrost."""

import logging
from time import time
from typing import Any

from pydantic import BaseModel, Field, ValidationError

_LOGGER = logging.getLogger(__name__)


class Envelope(BaseModel):
    """Envelope padrão para mensagens da Bifrost"""

    v: int
    src: str
    token: str
    dst: str | None = None
    type: str
    ts: float = Field(default_factory=time)
    payload: dict[str, Any] = Field(default_factory=dict)


def parse_envelope(message: str) -> Envelope | None:
    """Tenta converter strings em Envelope."""
    try:
        return Envelope.model_validate_json(message)
    except ValidationError as e:
        _LOGGER.debug("Mensagem com formato inválido: %s", e)
        return None
