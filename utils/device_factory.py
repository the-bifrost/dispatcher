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
    