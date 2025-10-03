"""Modelo padrão de dispositivos MQTT."""

from typing import Literal
from pydantic import BaseModel

class MqttAttributes(BaseModel):
    """Atributos base de dispostivos MQTT"""
    topic_in: str
    topic_out: str

class MqttDevice(BaseModel):
    """Um dispositivo que se comunica via MQTT."""
    protocol: Literal["mqtt"]
    device_id: str
    device_type: str
    attributes: MqttAttributes