"""
dispatcher/protocols/rest_api.py
Protocolo de API REST e WebSocket usando FastAPI.
"""
import asyncio
import logging
import json
from typing import List
import aiosqlite
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from core.event_bus import event_bus
from utils.envelope import Envelope
from utils.const import EventState


_LOGGER = logging.getLogger(__name__)


# --- Modelos de Configuração ---
class ApiConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    db_path: str = "config/db/devices.db" # Caminho para leitura (Query)

# --- Inicialização do FastAPI ---
app = FastAPI(title="Bifrost API", version="2.0.0")

# Configurar CORS (para permitir que seu Dashboard React/Vue acesse a API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique a URL do seu front
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variável global para guardar a config (necessário para as rotas acessarem o DB)
_API_CONFIG: ApiConfig | None = None

# --- Rotas da API ---

@app.get("/")
async def root():
    """Health Check."""
    return {"status": "online", "system": "Bifrost Dispatcher"}

@app.get("/devices")
async def get_devices():
    """
    Lista todos os dispositivos registrados.
    Lê diretamente do SQLite (CQRS - Leitura direta).
    """
    if not _API_CONFIG:
        raise HTTPException(status_code=500, detail="API não configurada")

    try:
        async with aiosqlite.connect(_API_CONFIG.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM devices") as cursor:
                rows = await cursor.fetchall()
                results = []
                for row in rows:
                    item = dict(row)
                    # Tenta parsear o JSON de config se existir
                    if item.get('config'):
                        try:
                            item['config'] = json.loads(item['config'])
                        except: 
                            pass
                    results.append(item)
                return results
    except Exception as e:
        _LOGGER.error("Erro ao ler DB na API: %s", e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages")
async def send_message(envelope: Envelope):
    """
    Endpoint para enviar um comando para algum dispositivo.
    O Frontend envia um JSON (Envelope), e a API joga no Barramento.
    """
    _LOGGER.info("API recebeu comando para: %s", envelope.dst)
    
    # Injeta no barramento como se fosse um evento de "Protocolo Recebeu algo"
    # Você pode criar um tópico específico ou usar o genérico de entrada
    # Aqui vamos publicar direto no tópico que o Router ouve, ou simular uma entrada
    
    # Opção A: Simular entrada (vai passar pelo Registry para validar)
    # await event_bus.publish("protocol.message_received", envelope)
    
    # Opção B: Se a API for considerada "Admin", pode mandar direto pro Router?
    # Melhor seguir o fluxo: Entrada -> Registry -> Router.
    await event_bus.publish("protocol.message_received", envelope)
    
    return {"status": "queued", "envelope": envelope}

# --- WebSocket para Real-Time ---

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
            except:
                pass # Lidar com conexões mortas

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Conexão persistente que recebe TUDO que passa no barramento.
    Útil para logs em tempo real no dashboard.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Mantém a conexão aberta. 
            # Se o front enviar algo pelo socket, recebemos aqui (opcional)
            data = await websocket.receive_text()
            # Pode implementar comandos via socket se quiser
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# --- Ponte EventBus -> WebSocket ---

async def bridge_event_to_websocket(data):
    """
    Callback genérico que pega qualquer evento do bus e manda pro WebSocket.
    """
    try:
        # Se o dado for um Envelope ou dict, serializa
        if isinstance(data, Envelope):
            msg = data.model_dump_json()
        elif isinstance(data, dict):
            msg = json.dumps(data, default=str)
        else:
            msg = str(data)
            
        await manager.broadcast(msg)
    except Exception as e:
        _LOGGER.error("Erro no bridge WebSocket: %s", e)

# --- Setup do Protocolo (Padrão Bifrost) ---

async def setup_protocol(raw_config: dict):
    """
    Função chamada pelo start.py para iniciar o servidor Uvicorn.
    """
    global _API_CONFIG
    try:
        config = ApiConfig(**raw_config)
        _API_CONFIG = config
    except Exception as e:
        _LOGGER.error("Configuração da API inválida: %s", e)
        return

    # Inscrever o WebSocket para ouvir eventos importantes
    # Você pode ouvir "state_changed", "device.validated", etc.
    # Para o dashboard ver tudo, vamos ouvir os principais:
    event_bus.subscribe("device.message_validated", bridge_event_to_websocket)
    event_bus.subscribe("device.unknown", bridge_event_to_websocket)
    # Se quiser ver o que está saindo também:
    # event_bus.subscribe(EventState.SEND_TO.value + "lora", bridge_event_to_websocket)

    # Configuração do Servidor Uvicorn para rodar DENTRO do loop atual
    u_config = uvicorn.Config(
        app=app, 
        host=config.host, 
        port=config.port, 
        log_level="info"
    )
    server = uvicorn.Server(u_config)

    _LOGGER.info("Iniciando API Server em http://%s:%s", config.host, config.port)
    
    # O server.serve() é uma corrotina bloqueante se não cuidada, 
    # mas o uvicorn foi feito para asyncio.
    # Vamos rodar ele como uma task no loop.
    await server.serve()