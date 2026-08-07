"""Logger de Histórico. Escuta eventos validados e persiste no SQLite em lote."""

import asyncio
import json
import logging
import sqlite3
from pathlib import Path

import aiosqlite

from ..core.event_bus import event_bus
from ..utils.device import Device
from ..utils.envelope import Envelope
from ..utils.events import Events

_LOGGER = logging.getLogger(__name__)

BATCH_SIZE = 50
FLUSH_INTERVAL = 5  # segundos


class History:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._queue: asyncio.Queue = asyncio.Queue()
        self._task: asyncio.Task | None = None

        # Inscreve-se para ouvir apenas mensagens que passaram pela validação do Registry
        event_bus.subscribe(Events.Device.VALIDATED, self.save_history)
        _LOGGER.info(
            "HistoryLogger iniciado e monitorando: %s", Events.Device.VALIDATED
        )

    def start(self):
        """Inicia a task de escrita em lote no SQLite."""
        self._task = asyncio.create_task(self._writer_loop())

    async def save_history(self, data: dict):
        """Enfileira o payload da mensagem para ser persistido em lote."""
        envelope: Envelope | None = data.get("envelope")
        device: Device | None = data.get("device")

        if not envelope or not device:
            _LOGGER.warning("Dados incompletos para salvar histórico: %s", data)
            return

        await self._queue.put((device.id, json.dumps(envelope.payload)))

    async def _writer_loop(self):
        """Mantém uma única conexão aberta e persiste registros em lote."""
        async with aiosqlite.connect(self.db_path) as db:
            while True:
                batch = []

                try:
                    item = await asyncio.wait_for(
                        self._queue.get(), timeout=FLUSH_INTERVAL
                    )
                    batch.append(item)
                except asyncio.TimeoutError:
                    continue

                while len(batch) < BATCH_SIZE:
                    try:
                        batch.append(self._queue.get_nowait())
                    except asyncio.QueueEmpty:
                        break

                await self._flush(db, batch)

    async def _flush(self, db: aiosqlite.Connection, batch: list[tuple[str, str]]):
        try:
            await db.executemany(
                "INSERT INTO history (device_id, payload) VALUES (?, ?)",
                batch,
            )
            await db.commit()
            _LOGGER.debug("Histórico persistido: %d registro(s)", len(batch))
        except sqlite3.Error as e:
            _LOGGER.error("Falha ao salvar histórico no banco: %s", e)
