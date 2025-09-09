"""Start Dispacher."""

import logging
import logging.config

from pathlib import Path

from core.dispatcher import Dispatcher
from protocols import MqttHandler, EspNowHandler
from utils.config_loader import load_config
from services.registry import DeviceRegistry

cfg = load_config("config/config.toml")

if not cfg:
    exit(1)

logger = logging.getLogger()


def setup_logging():
    logger_config = load_config(cfg["paths"]["logger_config"])
    logging.config.dictConfig(logger_config)


def main():
    """Start Dispatcher."""
    setup_logging()

    logger.info("Iniciando Dispatcher...")

    registry = DeviceRegistry(Path(__file__).parent / cfg["paths"]["device_registry"])
    
    handlers = {
        "mqtt": MqttHandler(cfg["mqtt"]["broker"], cfg["mqtt"]["port"]),
        "espnow": EspNowHandler(cfg["uart"]["ports"][1], cfg["uart"]["baudrate"]),
    }

    dispatcher = Dispatcher(registry=registry, handlers=handlers)

    logger.info("Dispatcher Iniciado!")

    try:
        while True:
            for handler in handlers.values():
                message = handler.read()

                if message:
                   dispatcher.dispatch(message)
    
    except KeyboardInterrupt:
        for handler in handlers.values():
            handler.close()

        logger.info("Encerrando Dispatcher...")    
        exit(1)


if __name__ == "__main__":
    """Start Dispatcher."""
    main()
