"""Padrão de Dispositivos da Bifrost."""

import logging
from typing import Any, Dict, Optional
from datetime import datetime

from pydantic import BaseModel, Field


_LOGGER = logging.getLogger(__name__)


class Device(BaseModel):
    """Modelo Base para Dispositivos da Bifrost."""
    id: str
    protocol: str
    token: Optional[str | bytes] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True