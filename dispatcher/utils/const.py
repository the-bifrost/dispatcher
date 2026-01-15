"""Eventos e Variáveis constantes da Bifrost."""
from enum import Enum

# eventos de telemetria
# sensor.reading_received, temperature.changed
class ProtocolEvent(Enum):
    MESSAGE_RECEIVED = "protocol.message_received"

class DeviceEvent(Enum):
    MESSAGE_VALIDATED = "device.message_validated"
    UNKNOWN = "device.unknown"
    REGISTER_REQUEST = "device.register_request"
    CONNECTED = "device.connected"
    DISCONNECTED = "device.disconnected"

# eventos de sistema
# component.loaded, system.startup
class SystemEvent(Enum):
    pass

# eventos de comando
# light.turn_on, message.send

# Legacy
class EventState(Enum):
    STATE_CHANGED = "state_changed"
    SEND_TO = "send_to_"