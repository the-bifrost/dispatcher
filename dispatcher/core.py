"""Looping Assíncrono da Bifrost."""

import asyncio
import logging
import logging.config
import signal

from pathlib import Path

from dispatcher.dispatcher import Dispatcher
from dispatcher.handlers import EspNowHandler, LoRaHandler, MqttHandler
from dispatcher.services.registry import DeviceRegistry
from dispatcher.utils.config_loader import load_config


_LOGGER = logging.getLogger(__name__)


def setup_logging():
    """Faz o setup da configuração de Logs do sistema."""
    logger_config = load_config(cfg["paths"]["logger_config"])
    _LOGGER.config.dictConfig(logger_config)


# async def read_loop(handler, dispatcher: Dispatcher):
#     """Uma tarefa de longe duração para ler mensagens de um handler e despachar"""

#     protocol_name = handler.protocol.upper()
#     _LOGGER.info(f"[{protocol_name}] Loop de leitura iniciado.")

#     try:
#         while True:
#             message = await handler.read()
#             if message:
#                 # O dispatcher agora processa a mensagem recebida
#                 await dispatcher.dispatch(message)
#     except asyncio.CancelledError:
#         # Exceção esperada durante o desligamento
#         _LOGGER.info(f"[{protocol_name}] Loop de leitura cancelado.")
#     except Exception:
#         # Captura qualquer outro erro inesperado no loop
#         _LOGGER.exception(f"[{protocol_name}] Erro irrecuperável no loop de leitura. A tarefa será encerrada.")


async def start(config_path: Path):
    """Inicia o Loop Principal da Dispatcher."""

    config_file = config_path / "config.toml"

    cfg = load_config(str(config_file))





    return
    # --- 1. CARREGAMENTO E CONFIGURAÇÃO INICIAL ---
    stop_event = asyncio.Event()

    # --- 2. CONFIGURAÇÃO DO SHUTDOWN GRACIOSO ---
    loop = asyncio.get_running_loop()

    def handle_signal(sig):
        """Função interna para lidar com sinais do SO."""
        _LOGGER.warning(f"Sinal de encerramento {sig.name} recebido.")
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal, sig)

    # --- 3. INICIALIZAÇÃO DOS COMPONENTES ---
    _LOGGER.info("Iniciando o serviço Bifrost Dispatcher...")
    
    registry = DeviceRegistry(Path(config_path).parent / cfg.paths.device_registry)
    
    # Cria uma lista com todos os handlers que queremos iniciar
    # Esta é a única parte que você precisa alterar para adicionar/remover protocolos
    handlers_to_start = [
        EspNowHandler(cfg.uart.ports[1], cfg.uart.baudrate),
        # LoraHandler(cfg.uart.ports[4], cfg.uart.baudrate), # Descomente para ativar
        MqttHandler(cfg.mqtt.broker, cfg.mqtt.port),
    ]
    
    # Inicia as conexões de todos os handlers em paralelo
    await asyncio.gather(*(handler.start() for handler in handlers_to_start))
    
    # Cria um dicionário de handlers ativos para o dispatcher
    active_handlers = {h.protocol: h for h in handlers_to_start}

    dispatcher = Dispatcher(registry=registry, handlers=active_handlers)
    
    # --- 4. CRIAÇÃO E EXECUÇÃO DAS TAREFAS ---
    _LOGGER.info("Iniciando loops de leitura para os protocolos ativos...")
    tasks = [
        asyncio.create_task(read_loop(handler, dispatcher))
        for handler in active_handlers.values()
    ]
    
    _LOGGER.info("Bifrost Dispatcher iniciado e operacional.")
    
    # --- 5. AGUARDA O SINAL DE PARADA ---
    await stop_event.wait()
    
    # --- 6. PROCESSO DE ENCERRAMENTO ---
    _LOGGER.info("Iniciando processo de encerramento...")
    
    # Cancela as tarefas de leitura
    for task in tasks:
        task.cancel()
    
    # Espera que todas as tarefas de leitura terminem seu cancelamento
    await asyncio.gather(*tasks, return_exceptions=True)
    
    # Fecha as conexões dos handlers em paralelo
    await asyncio.gather(*(handler.close() for handler in active_handlers.values()))

    # Aqui você pode adicionar o fechamento de outras conexões, como a do banco de dados
    # close_write_api()
    
    _LOGGER.info("Serviço encerrado de forma limpa.")