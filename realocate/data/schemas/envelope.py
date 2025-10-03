"""Esquema de Envelopes da Bifrost."""

from pydantic import BaseModel
from typing import Any, Dict
import time

class Envelope(BaseModel):
    """Envelope padrão para mensagens da Bifrost"""
    v: int
    protocol: str
    src: str
    dst: str
    type: str
    ts: int = int(time.time())
    payload: Dict[str, Any] = {}