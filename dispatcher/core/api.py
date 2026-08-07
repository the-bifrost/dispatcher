"""Dispatcher API."""

import asyncio
import json
import logging
import sqlite3

import aiosqlite
import uvicorn
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from ..core.device_registry import DeviceRegistry
from ..core.event_bus import event_bus
from ..core.state_machine import StateMachine
from ..engine.flow_runner import FlowRunner
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

                    if item.get("config"):
                        try:
                            item["config"] = json.loads(item["config"])
                        except json.JSONDecodeError:
                            _LOGGER.warning("Configuração JSON inválida ignorada")

                    if hasattr(item, "get") and item.get("token"):
                        try:
                            item.pop("token", None)
                        except AttributeError as e:
                            _LOGGER.warning(
                                "Falha ao remover token. Formato do dado inválido (esperado dicionário): %s",
                                e,
                            )
                    results.append(item)
                return results
    except sqlite3.Error as e:
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
            token=device.token,
        )

        _LOGGER.info("Novo dispositivo cadastrado via API: %s", device.id)

        return {"message": "Dispositivo cadastrado com sucesso", "device": device}

    except sqlite3.Error as e:
        _LOGGER.error("Erro ao cadastrar dispositivo via API: %s", e)
        raise HTTPException(status_code=500, detail=f"Erro interno ao salvar: {e!s}")


@app.post("/messages")
async def send_message(envelope: Envelope):
    """Injeta comandos no barramento."""
    _LOGGER.info("API recebeu comando para: %s", envelope.dst)
    await event_bus.publish("protocol.message_received", envelope)
    return {"status": "queued", "envelope": envelope}


# --- Estados dos dispositivos ---


@app.get("/states")
async def get_states(request: Request):
    """Retorna o último estado conhecido de todos os dispositivos."""
    state_machine: StateMachine = request.app.state.state_machine
    return state_machine.get_all_states()


@app.get("/states/{device_id}")
async def get_device_state(device_id: str, request: Request):
    """Retorna o último estado conhecido de um dispositivo."""
    state_machine: StateMachine = request.app.state.state_machine
    state = state_machine.get_state(device_id)

    if state is None:
        raise HTTPException(
            status_code=404, detail="Estado não encontrado para este dispositivo"
        )

    return state


# --- Automações (Flow Engine) ---


@app.get("/automations")
async def get_automations(request: Request):
    """Retorna o flow de automações atualmente carregado."""
    flow_runner: FlowRunner = request.app.state.flow_runner
    return flow_runner.get_flow()


@app.post("/automations")
async def update_automations(flow: dict, request: Request):
    """Salva um novo flow de automações e recarrega o engine sem reiniciar a Bifrost."""
    flow_runner: FlowRunner = request.app.state.flow_runner

    try:
        await flow_runner.save_and_reload(flow)
    except (OSError, ValueError) as e:
        _LOGGER.error("Erro ao salvar automações: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Automações atualizadas e recarregadas", "flow": flow}


# --- Websocket e Bridge ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except (RuntimeError, WebSocketDisconnect) as e:
                _LOGGER.warning(
                    "Falha ao enviar mensagem para cliente WebSocket. Conexão possivelmente encerrada: %s",
                    e,
                )


manager = ConnectionManager()


@app.websocket("/events")
async def events_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


def _serialize(data):
    """Converte Envelopes/Devices e estruturas aninhadas em algo JSON-serializável."""
    if isinstance(data, dict):
        return {key: _serialize(value) for key, value in data.items()}

    if hasattr(data, "model_dump"):
        return data.model_dump(mode="json")

    return data


def make_bridge(event_name: str):
    """Cria um callback que repassa eventos do EventBus para o WebSocket com um schema tipado."""

    async def bridge(data):
        try:
            message = json.dumps(
                {"event": event_name, "data": _serialize(data)}, default=str
            )
            await manager.broadcast(message)
        except Exception:
            _LOGGER.exception("Erro interno no bridge WebSocket (%s)", event_name)

    bridge.__name__ = f"bridge_{event_name}"
    return bridge


# --- Classe e Inicialização ---
class BifrostAPI:
    def __init__(
        self,
        host: str,
        port: int,
        registry: DeviceRegistry,
        state_machine: StateMachine,
        flow_runner: FlowRunner,
    ):
        self.host = host
        self.port = port
        app.state.registry = registry
        app.state.state_machine = state_machine
        app.state.flow_runner = flow_runner

    async def start(self):
        """Inicia o servidor de forma assíncrona."""
        event_bus.subscribe(Events.Device.VALIDATED, make_bridge("message"))
        event_bus.subscribe(Events.Device.UNKNOWN, make_bridge("unknown"))
        event_bus.subscribe(Events.Device.STATE_CHANGED, make_bridge("state_changed"))

        config = uvicorn.Config(
            app=app, host=self.host, port=self.port, log_level="warning"
        )
        server = uvicorn.Server(config)

        _LOGGER.info("Core API iniciada em http://%s:%s", self.host, self.port)
        asyncio.create_task(server.serve())
