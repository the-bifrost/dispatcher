"""Registro de Dispositivos da Dispatcher."""
import logging
import json
from pathlib import Path

import aiosqlite

from core.event_bus import event_bus
from utils.envelope import Envelope


_LOGGER = logging.getLogger(__name__)


# Eventos
EVENT_PROTOCOL_RECEIVED = "protocol.message_received"
EVENT_DEVICE_VALIDATED = "device.message_validated"
EVENT_DEVICE_UNKNOWN = "device.unknown"


class DeviceRegistry:
    def __init__(self, db_path: Path, schema_path: Path):
        self.db_path = db_path
        self.schema_path = schema_path

        # Inscreve-se para ouvir mensagens brutas dos protocolos
        event_bus.subscribe(EVENT_PROTOCOL_RECEIVED, self.handle_protocol_message)

    async def initialize(self):
        """Inicializa o banco de dados."""
        if not self.schema_path.exists():
            _LOGGER.error("Arquivo de schema do banco de dados não encontrado: %s", self.schema_path)
            return
        
        try:
            schema_sql = self.schema_path.read_text(encoding="utf-8")

            async with aiosqlite.connect(self.db_path) as db:
                await db.executescript(schema_sql)
                await db.commit()
            _LOGGER.info("DeviceRegistry inicializado com SQLite: %s", self.db_path)
        
        except Exception as e:
            _LOGGER.exception("Erro fatal ao inicializar DB: %s", e)

    async def get_device(self, device_id: str) -> dict | None:
        """Busca dispositivo no banco pelo ID."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Assume que 'id' no banco bate com o 'src' do envelope
            async with db.execute("SELECT * FROM devices WHERE id = ?", (device_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)
                    # Desserializa a config (JSON string -> Dict)
                    if 'config' in data and isinstance(data['config'], str):
                        try:
                            data['config'] = json.loads(data['config'])
                        except json.JSONDecodeError:
                            data['config'] = {}
                    return data
        return None

    async def handle_protocol_message(self, envelope: Envelope):
        """
        Callback acionado pelo EventBus.
        1. Recebe envelope bruto.
        2. Consulta SQLite.
        3. Publica resultado (Validado ou Desconhecido).
        """
        sender_id = envelope.src
        device = await self.get_device(sender_id)

        if device:
            _LOGGER.debug("Dispositivo autenticado via DB: %s", sender_id)
            # Publica o evento de sucesso com os dados do banco anexados
            await event_bus.publish(EVENT_DEVICE_VALIDATED, {
                "envelope": envelope,
                "device": device
            })
        else:
            _LOGGER.warning("Dispositivo não registrado no DB: %s", sender_id)
            await event_bus.publish(EVENT_DEVICE_UNKNOWN, envelope)

    async def add_device(self, device_id: str, protocol: str, config: dict, token: str | None = None):
        """Adiciona Dispositivos Dinamicamente."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO devices (id, protocol, config, token) VALUES (?, ?, ?, ?)",
                (device_id, protocol, json.dumps(config), token)
            )
            await db.commit()
            _LOGGER.info("Dispositivo %s salvo no banco.", device_id)