"""Classe base para os Handlers Bifrost"""

from abc import ABC, abstractmethod
from typing import Optional

from models.devices import Device
from utils.envelope import Envelope

class BaseHandler(ABC):
    """Contrato para todos os handlers de protocolo"""

    @property
    @abstractmethod
    def protocol(self) -> str:
        """Retorna o nome do protocolo que o handler gerencia"""
        pass

    @abstractmethod
    async def start(self):
        """Inicializa a conexão assíncrona"""
        pass

    @abstractmethod
    async def read(self) -> Envelope | None:
        """Retorna mensagens válidas, no padrão envelope."""
        pass
    
    @abstractmethod
    async def write(self, envelope: Envelope, device: Device) -> bool:
        """Recebe um envelope e envia a mensagem, internamente."""
        pass

    @abstractmethod
    def close(self):
        pass