"""Serviço para interagir com o banco e registrar dispositivos."""

import logging

from dispatcher.data.database import SessionLocal
from dispatcher.data.models.device import Device as DeviceModel
from dispatcher.data.schemas.devices import Device as DeviceSchema

_LOGGER = logging.getLogger(__name__)

def register_new_device(device: DeviceSchema):

    try:
        db_device = DeviceModel(**device.model_dump())
        db = SessionLocal()

        try:
            db.add(db_device)
            db.commit()
        finally:
            db.close()

    except Exception as e:
        _LOGGER.error("Erro ao registrar dispositivo: %s", e)