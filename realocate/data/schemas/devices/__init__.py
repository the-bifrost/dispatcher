"""Modelo de padrão de dispositivos."""

from typing import Union, Annotated
from pydantic import Field

from .LoraDevice import LoraDevice
from .MqttDevice import MqttDevice
from .EspNowDevice import EspNowDevice


Device = Annotated[
    Union[EspNowDevice, MqttDevice, LoraDevice],
    Field(discriminator='protocol')
]