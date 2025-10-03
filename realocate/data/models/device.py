"""Modelo de Dispositivo no Banco de Dados"""

from sqlalchemy import Column, Integer, String, JSON

from ..database import Base

class Device(Base):
    """Tabela Única para registrar todos os dispositivos conhecidos."""

    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True, nullable=False)
    protocol = Column(String, nullable=False)

    # Salva os atributos dos dispositivos dentro de um JSONB
    attributes = Column(JSON, nullable=True)