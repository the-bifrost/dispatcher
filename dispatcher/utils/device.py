"""Padrão de Dispositivos da Bifrost."""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

_LOGGER = logging.getLogger(__name__)


class Device(BaseModel):
    """Modelo Base para Dispositivos da Bifrost."""

    id: str
    protocol: str
    token: str | bytes | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None

    class Config:
        from_attributes = True
