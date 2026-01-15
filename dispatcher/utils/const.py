"""Eventos e Variáveis constantes da Bifrost."""
from enum import Enum

# eventos de telemetria
# sensor.reading_received, temperature.changed

# eventos de sistema
# component.loaded, system.startup, device.connected, device.disconnected

# eventos de comando
# light.turn_on, message.send

# Atual
class EventState(Enum):
    STATE_CHANGED = "state_changed"
    SEND_TO = "send_to_"