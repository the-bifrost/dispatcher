"""Factory para modelo de Dispositivos"""

import logging
from typing import Dict, Any, Optional

from pydantic import TypeAdapter, ValidationError

from models.devices import Device

logger = logging.getLogger(__name__)

# Cria um validador global para registrar os dispositivos
try:
    DEVICE_VALIDATOR = TypeAdapter(Device)
    logger.info("Validador de dispositivos criado com sucesso.")
except Exception as e:
    logger.error("Falha ao criar o validador de dispositivos: %s", e)
    DEVICE_VALIDATOR = None


def create_device(device_data: Dict[str, Any]) -> Device | None:
    """Valida e cria um dispositivo"""

    if not DEVICE_VALIDATOR:
        logger.error("O validador de dispositivos não está disponível.")
        return None
    
    try:
        return DEVICE_VALIDATOR.validate_python(device_data)
    except ValidationError:
        logger.warning("Dados de dispositivo inválidos foram ignorados: %s", device_data)
        return None
    

if __name__ == "__main__":
    
    espnow_data = {
        "protocol":"espnow",
        "device_type":"test",
        "address":"AA:BB:CC:DD"
    }

    # Teste com dados válidos
    esp_device = create_device(espnow_data)
    if esp_device:
        print(f"Sucesso! Objeto criado: {esp_device}")
        print(f"Tipo do objeto: {type(esp_device)}")
    else:
        print("Falha ao criar o dispositivo LoRa.")

    # Teste com dados inválidos
    invalid_mqtt_data = {
        "protocol":"mqtt",
        "device_type":"test",
        "topic":"sensors/mqtt/device"
    }

    mqtt_device = create_device(invalid_mqtt_data)
    if esp_device:
        print(f"Sucesso! Objeto criado: {esp_device}")
        print(f"Tipo do objeto: {type(esp_device)}")
    else:
        print("Falha esperada. A função retornou None para o dispositivo inválido.")