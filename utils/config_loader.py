"""Módulo de carregamento de configurações a partir de arquivos TOML.

Este módulo define:
- DotDict: uma subclasse de dict que permite acesso a chaves via notação de atributo.
- load_config: função estática para ler um arquivo TOML e retornar um objeto DotDict.
"""  

from pathlib import Path
import toml

class DotDict(dict):
    """Dicionário que permite acesso às chaves através de atributos.

    Exemplo:
        cfg = DotDict({'uart': {'ports': ["/dev/ttyS0"], 'baud_rate': 9600}})
        print(cfg.uart.ports)  # ['/dev/ttyS0']
    """
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
    """Carrega um arquivo de configuração no formato TOML e retorna um DotDict.

    Args:
        path (str): Caminho relativo ao diretório base do projeto até o arquivo TOML.

    Returns:
        DotDict: Estrutura de configuração com acesso via atributos.

    Exemplo:
        cfg = load_config("config/config.toml")
        print(cfg.mqtt.broker)
        # imprime o broker configurado no TOML
    """

    config_path = Path(__file__).parent.parent / path

    with config_path.open("r", encoding="utf-8") as f:
        data = toml.load(f)

    return DotDict(data)
