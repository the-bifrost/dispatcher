"""Módulo para carregar configurações."""

from pathlib import Path
import toml


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


@staticmethod
def load_config(path: str) -> DotDict:
    """Carrega um arquivo TOML e retorna um DotDict."""

    with open(path, "r", encoding="utf-8") as f:
        data = toml.load(f)

    return DotDict(data)
