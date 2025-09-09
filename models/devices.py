"""Modelo de padrão de dispositivos."""

from typing import Literal, Union, Annotated
from pydantic import BaseModel, Field
from abc import ABC, abstractmethod

class BaseDevice(BaseModel, ABC):
    """Modelo base para qualquer dispositivo no registro."""
    device_type: str

    @property
    @abstractmethod
    def destination(self) -> str:
        """É a função que retorna o endereço/tópico/canal para este dispositivo."""
        pass

class EspNowDevice(BaseDevice):
    """Um dispositivo que se comunica via ESP-NOW."""
    protocol: Literal["espnow"]
    address: str

    @property
    def destination(self) -> str:
        """Retorna o endereço de destino para este tipo de dispositivo."""
        return self.address

class MqttDevice(BaseDevice):
    """Um dispositivo ou tópico que se comunica via MQTT."""
    protocol:Literal["mqtt"]
    topic: str

    @property
    def destination(self) -> str:
        """Retorna o endereço de destino para este tipo de dispositivo."""
        return self.topic

Device = Annotated[
    Union[EspNowDevice, MqttDevice],
    Field(discriminator='protocol')
]