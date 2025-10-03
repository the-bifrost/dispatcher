"""Serviço para interagir com o banco e registrar Envelopes."""

import logging

from dispatcher.data.database import SessionLocal
from dispatcher.data.models.envelope import Envelope as EnvelopeModel
from dispatcher.data.schemas.envelope import Envelope as EnvelopeSchema

_LOGGER = logging.getLogger(__name__)

def register_new_envelope(envelope: EnvelopeSchema):

    try:
        db_device = EnvelopeModel(**envelope.model_dump())
        db = SessionLocal()

        try:
            db.add(db_device)
            db.commit()
        finally:
            db.close()

    except Exception as e:
        _LOGGER.error("Erro ao registrar dispositivo: %s", e)