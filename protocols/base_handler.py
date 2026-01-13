"""Classe base para os Handlers Bifrost"""

from abc import ABC, abstractmethod

from models.devices import Device
from utils.envelope import Envelope

class BaseHandler(ABC):
    """Contrato para todos os handlers de protocolo"""

    @abstractmethod
    def read(self) -> Envelope | None:
        """Retorna mensagens válidas, no padrão envelope."""
        pass
    
    @abstractmethod
    def write(self, envelope: Envelope, device: Device) -> bool:
        """Recebe um envelope e envia a mensagem, internamente."""
        pass

    @abstractmethod
    def close(self):
        pass