"""Modelo de padrão de dispositivos."""

from typing import Literal, Union, Annotated, Optional
from pydantic import BaseModel, Field

class BaseDevice(BaseModel):
    """Modelo base para qualquer dispositivo no registro."""
    protocol: str
    device_type: str

class EspNowDevice(BaseDevice):
    """Um dispositivo que se comunica via ESP-NOW."""
    protocol: Literal["espnow"]
    address: str

class MqttDevice(BaseDevice):
    """Um dispositivo ou tópico que se comunica via MQTT."""
    protocol:Literal["mqtt"]
    topic: str

Device = Annotated[
    Union[EspNowDevice, MqttDevice],
    Field(discriminator='protocol')
]