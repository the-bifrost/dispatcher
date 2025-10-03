"""Classe para parâmetros de configuração."""

import logging
import sys

from pydantic_settings import BaseSettings, SettingsConfigDict


_LOGGER = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Carrega informações de um arquivo .env, caso não existir, salva como um valor padrão."""
    # Configuração do pydantic_settings
    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

    # Caminhos de Arquivos
    PATH_DEVICE_REGISTRY: str = "devices.json"
    PATH_LOGGER_CONFIG: str = "logs.toml"

    # # Configurações do Banco de Daodos.
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str
    DATABASE_DB: str
    DATABASE_PASSWORD: str
    DATABASE_URL: str

    # Configurações do broker MQTT
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883

    # Configurações de UART
    UART_BAUDRATE: int = 9600

    # - "/dev/ttyS0"
    UART_PORT_ESPNOW: str = "/dev/ttyAMA2"
    # - "/dev/ttyAMA3" 
    # - "/dev/ttyAMA4"
    UART_PORT_LORA: str = "/dev/ttyAMA5"


# Cria uma única instância de Settings(), acessível para todos os módulos.
try:
    settings = Settings()
    _LOGGER.debug(settings)
except Exception as e:
    _LOGGER.fatal("Erro de configuração - %s", e)
    sys.exit(1)
