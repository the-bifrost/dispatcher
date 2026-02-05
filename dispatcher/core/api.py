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
from pydantic import BaseModel

from ..core.event_bus import event_bus
from ..core.device_registry import DeviceRegistry
from ..utils.device import Device
from ..utils.envelope import Envelope
from ..utils.events import Events
from ..utils.token import generate_token


_LOGGER = logging.getLogger(__name__)

class RouteModel(BaseModel):
    """Modelo para criação e exibição de rotas."""
    source_id: str
    target_id: str
    enabled: bool = True


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

                    if item.get('token'):
                        try:
                            item.pop('token', None)
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

# --- Rotas de Gerenciamento de Rotas ---

@app.get("/routes")
async def get_routes(request: Request):
    """
    Retorna todas as conexões de roteamento configuradas no sistema.
    """
    registry: DeviceRegistry = request.app.state.registry

    try:
        async with aiosqlite.connect(registry.db_path) as db:
            db.row_factory = aiosqlite.Row
            # Seleciona todas as rotas da tabela definida no seu schema
            async with db.execute("SELECT * FROM routes") as cursor:
                rows = await cursor.fetchall()

                results = []
                
                for row in rows:
                    results.append(dict(row))
                return results
    except Exception as e:
        _LOGGER.error("Erro ao ler rotas do banco de dados: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar rotas: {str(e)}")
    

@app.post("/routes", status_code=201)
async def create_route(route: RouteModel, request: Request):
    """
    Cria ou atualiza uma rota de comunicação entre dois dispositivos.
    """
    registry: DeviceRegistry = request.app.state.registry

    try:
        async with aiosqlite.connect(registry.db_path) as db:
            # Habilita chaves estrangeiras para respeitar as restrições do schema
            await db.execute("PRAGMA foreign_keys = ON")
            
            # Usa INSERT OR REPLACE para lidar com a restrição UNIQUE(source_id, target_id)
            query = """
                INSERT OR REPLACE INTO routes (source_id, target_id, enabled)
                VALUES (?, ?, ?)
            """
            await db.execute(query, (route.source_id, route.target_id, int(route.enabled)))
            await db.commit()
            
        _LOGGER.info("Rota configurada: %s -> %s (Ativa: %s)", 
                     route.source_id, route.target_id, route.enabled)
        
        return {"message": "Rota configurada com sucesso", "route": route}
        
    except aiosqlite.IntegrityError as e:
        # Erro comum: tentar criar rota para dispositivo que não existe no banco
        _LOGGER.error("Erro de integridade ao criar rota: %s", e)
        raise HTTPException(
            status_code=400, 
            detail="Erro de integridade: Verifique se os IDs dos dispositivos existem no banco."
        )
    except Exception as e:
        _LOGGER.error("Erro ao salvar rota: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

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