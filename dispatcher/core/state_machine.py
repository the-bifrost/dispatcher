"""State Machine da Bifrost. Mantém o último estado conhecido de cada dispositivo."""

import json
import logging
from pathlib import Path

import aiosqlite

from ..core.event_bus import event_bus
from ..utils.device import Device
from ..utils.envelope import Envelope
from ..utils.events import Events

_LOGGER = logging.getLogger(__name__)


class StateMachine:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._states: dict[str, dict] = {}

        # Atualiza o estado sempre que uma mensagem validada chega
        event_bus.subscribe(Events.Device.VALIDATED, self.handle_validated)

        _LOGGER.info("StateMachine inicializada.")

    async def restore(self):
        """Carrega do SQLite o último estado conhecido de cada dispositivo."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT device_id, state, attributes FROM device_states"
            ) as cursor:
                async for row in cursor:
                    data = dict(row)
                    self._states[data["device_id"]] = {
                        "state": data["state"],
                        "attributes": json.loads(data["attributes"] or "{}"),
                    }

        _LOGGER.info("Estado restaurado para %d dispositivo(s)", len(self._states))

    async def handle_validated(self, data: dict):
        """Callback do EventBus: atualiza o estado a partir de uma mensagem validada."""
        envelope: Envelope | None = data.get("envelope")
        device: Device | None = data.get("device")

        if not envelope or not device:
            _LOGGER.warning("Dados incompletos para atualizar estado: %s", data)
            return

        await self.set_state(device.id, envelope.type, envelope.payload)

    async def set_state(self, device_id: str, state: str, attributes: dict | None = None):
        """Atualiza o estado em memória, persiste no SQLite e dispara STATE_CHANGED."""
        attributes = attributes or {}
        old_state = self._states.get(device_id)
        new_state = {"state": state, "attributes": attributes}
        self._states[device_id] = new_state

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO device_states (device_id, state, attributes, last_changed)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(device_id) DO UPDATE SET
                    state=excluded.state,
                    attributes=excluded.attributes,
                    last_changed=excluded.last_changed
                """,
                (device_id, state, json.dumps(attributes)),
            )
            await db.commit()

        await event_bus.publish(
            Events.Device.STATE_CHANGED,
            {
                "device_id": device_id,
                "old_state": old_state,
                "new_state": new_state,
            },
        )

    def get_state(self, device_id: str) -> dict | None:
        """Retorna o último estado conhecido de um dispositivo (em memória)."""
        return self._states.get(device_id)

    def get_all_states(self) -> dict[str, dict]:
        """Retorna o último estado conhecido de todos os dispositivos."""
        return dict(self._states)
