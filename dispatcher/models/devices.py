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
        """Retorna o endereço MAC do dispositivo de destino."""
        return self.address

class MqttDevice(BaseDevice):
    """Um dispositivo ou tópico que se comunica via MQTT."""
    protocol:Literal["mqtt"]
    topic_in: str
    topic_out: str

    @property
    def destination(self) -> str:
        """Retorna o tópico que o destino espera dados."""
        return self.topic_out
    
class LoraDevice(BaseDevice):
    """Um dispositivo que se Comunica via LoRa."""
    protocol:Literal["lora"]
    device_id: str

    @property
    def destination(self) -> str:
        """Retorna o id do dispositivo."""
        return self.device_id

Device = Annotated[
    Union[EspNowDevice, MqttDevice, LoraDevice],
    Field(discriminator='protocol')
]