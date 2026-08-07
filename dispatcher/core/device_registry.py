"""Registro de Dispositivos da Dispatcher."""

import json
import logging
from pathlib import Path

import aiosqlite
from pydantic import ValidationError

from ..core.event_bus import event_bus
from ..utils.device import Device
from ..utils.envelope import Envelope
from ..utils.events import Events
from ..utils.token import hash_token, verify_token

_LOGGER = logging.getLogger(__name__)


class DeviceRegistry:
    def __init__(self, db_path: Path):
        _LOGGER.info("Inicializando o DeviceRegistry")

        self.db_path = db_path

        # Inscreve-se para ouvir mensagens brutas dos protocolos
        event_bus.subscribe(Events.Protocol.RECEIVED, self.handle_protocol_message)

        _LOGGER.info("Registry Inicializado!")

    async def get_device(self, device_id: str) -> Device | None:
        """Busca dispositivo no banco pelo ID e retorna um Device."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Assume que 'id' no banco bate com o 'src' do envelope
            async with db.execute(
                "SELECT * FROM devices WHERE id = ?", (device_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)

                    if "config" in data and isinstance(data["config"], str):
                        try:
                            data["config"] = json.loads(data["config"])
                        except json.JSONDecodeError:
                            data["config"] = {}

                    if data.get("config") is None:
                        data["config"] = {}

                    try:
                        return Device(**data)
                    except ValidationError as e:
                        _LOGGER.error(
                            f"Erro ao converter dados do banco para modelo Device: {e}"
                        )
                        return None
        return None

    async def handle_protocol_message(self, envelope: Envelope):
        """Calback acionado pelo EventBus, recebe envelope bruto, consulta SQLite, publica resultado."""
        sender_id = envelope.src
        device = await self.get_device(sender_id)

        if not device:
            _LOGGER.warning("Dispositivo não registrado no DB: %s", sender_id)
            await event_bus.publish(Events.Device.UNKNOWN, envelope)
            return

        if device.token and not verify_token(envelope.token, device.token):
            _LOGGER.error("Falha de Autenticação: Token Inválido para %s", sender_id)
            await event_bus.publish(Events.Device.UNKNOWN, envelope)
            return

        _LOGGER.debug("Dispositivo autenticado com sucesso: %s", sender_id)
        await event_bus.publish(
            Events.Device.VALIDATED, {"envelope": envelope, "device": device}
        )

    async def add_device(
        self, device_id: str, protocol: str, config: dict, token: str | None = None
    ):
        """Adiciona Dispositivos Dinamicamente."""

        hashed_token = hash_token(token) if token else None

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO devices (id, protocol, config, token) VALUES (?, ?, ?, ?)",
                (device_id, protocol, json.dumps(config), hashed_token),
            )
            await db.commit()
            _LOGGER.info("Dispositivo %s salvo no banco.", device_id)
