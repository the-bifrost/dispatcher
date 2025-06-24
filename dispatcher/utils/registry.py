import json
from pathlib import Path

class DeviceRegistry():
    """Uma classe para manter registro de dispositivos em um arquivo JSON.

    Atributos
    ---------
    path : str
        O caminho até o arquivo json usado para registrar.
    _registry : dict
        O dicionário para manter o registro de dispositivos localmente.
    """

    def __init__(self, path: str):
        """Lê e salva localmente o JSON de configuração
        
        Faz a leitura dos dados, caso existam. Caso contrário, inicia um json vazio. 

        Parâmetros
        ----------
        path : str
            O caminho até o arquivo json usado para registrar.
        """

        self.path = Path(path)
        self._registry: dict = {}

        if self.path.exists():
            try:
                with self.path.open('r', encoding='utf-8') as f:
                    self._registry = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Arquivo JSON inválido: {e}")

        else:
            self._registry = {}
            self.save()

    def save(self) -> None:
        """Salva o registro local em um arquivo JSON
        
        Se o arquivo não existir, cria.
        """
        with self.path.open('w', encoding='utf-8') as f:
            json.dump(self._registry, f, indent=2, ensure_ascii=False)


    def get_by_id(self, device_id: str) -> dict | None:
        """Retorna as informações de dispositivos cadastrados
        
        Recebe um id e busca na lista de cadastrados, se existir,
        retorna um dicionário com as informações do dispositivo.

        Se não existir, retorna None

        """

        return self._registry.get(device_id)
    
    def get_by_address(self, address: str) -> dict | None:
        """Retorna as informações de dispositivos cadastrados a partir do adress
        
        Recebe um adress/topic e busca na lista de cadastrados, se existir,
        retorna um dicionário com as informações do dispositivo.

        Se não existir, retorna None

        """
        for id, info in self._registry.items():
            if info.get("address") == address or info.get("topic") == address:
                return info
        return None

    def add(self, device_id: str, address: str, protocol: str, **kwargs) -> dict:
        """ Adiciona um dispositivo no registro de dispositivos.

        Obrigatóriamente recebe um id, protocolo e adress/topic.

        Se as informações mínimas forem preenchidas, tenta cadastrar e retorna o status.
        """

        if device_id in self._registry:
            print(f"[REGISTRY] Device '{device_id}' já existe no registro.")

            return {
                "status": "already_registered",
                "message": f"Device '{device_id}' já está registrado.",
                "device_id": device_id
            }

        
        self._registry[device_id] = {
            "address": address,
            "protocol": protocol,
            **kwargs
        }
    
        self.save()

        return {
            "status": "success",
            "message": f"Device '{device_id}' registrado com sucesso.",
            "device_id": device_id
        }