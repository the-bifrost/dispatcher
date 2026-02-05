"""Dispatcher API."""

import asyncio
import logging
import json
from typing import List
from pathlib import Path

import aiosqlite
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from ..core.event_bus import event_bus
from ..core.device_registry import DeviceRegistry
from ..utils.device import Device
from ..utils.envelope import Envelope
from ..utils.events import Events
from ..utils.token import generate_token


_LOGGER = logging.getLogger(__name__)


app = FastAPI(title="Bifrost API", version="2.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Rotas da API ---
@app.get("/")
async def root():
    return {"status": "online", "system": "Bifrost Dispatcher"}


@app.get("/devices")
async def get_devices(request: Request):
    """Lista dispositivos usando a instância do registry injetada no app.state."""
    registry: DeviceRegistry = request.app.state.registry

    try:
        async with aiosqlite.connect(registry.db_path) as db:
            db.row_factory = aiosqlite.Row

            async with db.execute("SELECT * FROM devices") as cursor:
                rows = await cursor.fetchall()

                results = []

                for row in rows:
                    item = dict(row)

                    if item.get('config'):
                        try:
                            item['config'] = json.loads(item['config'])
                        except: pass
                    results.append(item)
                return results
    except Exception as e:
        _LOGGER.error("Erro ao ler banco de dados na api: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/devices", status_code=201)
async def register_new_device(request: Request, device: Device):
    """Cadastra um novo dispositivo no banco de dados."""
    registry: DeviceRegistry = request.app.state.registry

    if not device.token:
        device.token = generate_token()

    try:
        await registry.add_device(
            device_id=device.id,
            protocol=device.protocol,
            config=device.config,
            token=device.token
        )

        _LOGGER.info("Novo dispositivo cadastrado via API: %s", device.id)
        
        return {
            "message": "Dispositivo cadastrado com sucesso",
            "device": device
        }

    except Exception as e:
        _LOGGER.error("Erro ao cadastrar dispositivo via API: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar: {str(e)}") 

@app.post("/messages")
async def send_message(envelope: Envelope):
    """Injeta comandos no barramento."""
    _LOGGER.info("API recebeu comando para: %s", envelope.dst)
    await event_bus.publish("protocol.message_received", envelope)
    return {"status": "queued", "envelope": envelope}

# --- Websocket e Bridge ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except: pass

manager = ConnectionManager()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def bridge_event_to_websocket(data):
    """Ponte EventBus -> WebSocket."""
    try:
        if isinstance(data, dict) and "envelope" in data:
            msg = data["envelope"].model_dump_json()
        elif hasattr(data, 'model_dump_json'):
            msg = data.model_dump_json()
        else:
            msg = json.dumps(data, default=str)
        await manager.broadcast(msg)
    except Exception as e:
        _LOGGER.error("Erro no bridge WebSocket: %s", e)

# --- Classe e Inicialização ---
class BifrostAPI:
    def __init__(self, host: str, port: int, registry: DeviceRegistry):
        self.host = host
        self.port = port
        app.state.registry = registry

    async def start(self):
        """Inicia o servidor de forma assíncrona."""
        event_bus.subscribe(Events.Device.VALIDATED, bridge_event_to_websocket)
        event_bus.subscribe(Events.Device.UNKNOWN, bridge_event_to_websocket)

        config = uvicorn.Config(app=app, host=self.host, port=self.port, log_level="warning")
        server = uvicorn.Server(config)

        _LOGGER.info("Core API iniciada em http://%s:%s", self.host, self.port)
        asyncio.create_task(server.serve())