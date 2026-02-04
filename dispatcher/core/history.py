"""Logger de Histórico. Escuta eventos validados e persiste no SQLite."""

import json
import logging
from pathlib import Path

import aiosqlite

from ..core.event_bus import event_bus
from ..utils.events import Events
from ..utils.envelope import Envelope
from ..utils.device import Device


_LOGGER = logging.getLogger(__name__)


class HistoryLogger:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        # Inscreve-se para ouvir apenas mensagens que passaram pela validação do Registry
        event_bus.subscribe(Events.Device.VALIDATED, self.save_history)
        _LOGGER.info("HistoryLogger iniciado e monitorando: %s", Events.Device.VALIDATED)

    async def save_history(self, data: dict):
        """Salva o payload da mensagem na tabela de history."""
        envelope: Envelope | None = data.get("envelope")
        device: Device | None = data.get("device")

        if not envelope or not device:
            _LOGGER.warning("Dados incompletos para salvar histórico: %s", data)
            return

        # O payload é um dicionário, precisamos converter para string JSON para o SQLite
        payload_str = json.dumps(envelope.payload)

        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Segue a estrutura definida no seu schema.sql
                await db.execute(
                    "INSERT INTO history (device_id, payload) VALUES (?, ?)",
                    (device.id, payload_str)
                )
                await db.commit()
            _LOGGER.debug("Histórico persistido para o dispositivo: %s", device.id)
            
        except Exception as e:
            _LOGGER.error("Falha ao salvar histórico no banco: %s", e)
