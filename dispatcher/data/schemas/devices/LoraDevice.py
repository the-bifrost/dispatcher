"""Modelo padrão de dispositivos LoRa"""

from typing import Literal
from pydantic import BaseModel

class LoraAttributes(BaseModel):
    """Atributos base de dispostivos LoRa."""
    id: str

class LoraDevice(BaseModel):
    """Um dispositivo que se comunica via LoRa."""
    protocol: Literal["lora"]
    device_id: str
    device_type: str
    attributes: LoraAttributes