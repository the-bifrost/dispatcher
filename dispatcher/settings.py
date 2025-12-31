"""Parâmetros de Configuração."""

import logging
import sys

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
import yaml


_LOGGER = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Carrega informações de um arquivo .env, caso não existir, salva como um valor padrão."""

    # Caminhos de Arquivos
    PATH_DEVICE_REGISTRY: str = "devices.json"
    PATH_LOGGER_CONFIG: str = "logs.yaml"

    # env_file='.env' carrega as variáveis de ambiente
    # extra='allow' permite carregar tudo o que estiver no Yaml 
    model_config = SettingsConfigDict(env_file=".env", extra='allow')


def load_config_file(path: Path) -> dict:
    if not path.is_file():
        raise FileExistsError("Configuração não encontrada em: %s", path)
    
    content = path.read_text(encoding="utf-8")
    return yaml.safe_load(content) or {}


def load_configuration(path: Path) -> Settings:
    try:
        config_file_data = load_config_file(path)
        return Settings(**config_file_data)
    except Exception as e:
        # Caso tenha algum erro, mata o programa, para evitar configurações incorretas
        _LOGGER.fatal("Erro de configuração - %s", e)
        sys.exit(1)
