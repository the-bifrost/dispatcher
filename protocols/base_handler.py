"""Classe base para os Handlers Bifrost"""

from abc import ABC, abstractmethod

class BaseHandler(ABC):
    """Contrato para todos os handlers de protocolo"""

    @abstractmethod
    def read(self):
        pass
    
    @abstractmethod
    def write(self):
        pass

    @abstractmethod
    def close(self):
        pass