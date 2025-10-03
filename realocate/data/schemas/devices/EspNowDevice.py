"""Modelo padrão de dispositivos EspNow."""

from typing import Literal
from pydantic import BaseModel

class EspNowAttributes(BaseModel):
    """Atributos base de dispostivos ESPNOW."""
    address: str

class EspNowDevice(BaseModel):
    """Um dispositivo que se comunica via ESP-NOW."""
    protocol: Literal["espnow"]
    device_id: str
    device_type: str
    attributes: EspNowAttributes
