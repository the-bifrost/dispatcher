"""Módulo para carregar configurações."""

import logging

from pathlib import Path
import toml


_LOGGER = logging.getLogger(__name__)


class DotDict(dict):
    """Dicionário que permite acesso às chaves através de atributos."""
    def __getattr__(self, name):
        value = self.get(name)

        if isinstance(value, dict):
            value = DotDict(value)
            self[name] = value

        return value
    
    def __repr__(self):
        return f"DotDict({super().__repr__()})"


def load_config(path: Path) -> DotDict:
    """Carrega um arquivo TOML a partir de um objeto Path e retorna um DotDict."""
    try:
        with path.open("r", encoding="utf-8") as f:
            data = toml.load(f)
        return DotDict(data)
    except FileNotFoundError:
        _LOGGER.error("O arquivo de configuração não foi encontrado em '%'", path)
        raise
    except Exception as e:
        _LOGGER.error("Erro ao ler ou interpretar o arquivo de configuração '%s': %e", path, e)
        raise
