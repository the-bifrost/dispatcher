from pathlib import Path

DEVICE_REGISTRY_PATH = Path(__file__).parent / "devices.json"

UART_PORTS = [
  '/dev/ttyS0',
  '/dev/ttyAMA2',
  '/dev/ttyAMA3', #ESP-NOW
  '/dev/ttyAMA4',
  '/dev/ttyAMA5' #LoRa
]

BAUD_RATE = 9600
MQTT_BROKER = "localhost"
MQTT_PORT = 1883