"""Modelo de Envelope no Banco de Dados"""

from sqlalchemy import Column, Integer, String, JSON, DateTime, func

from ..database import Base

class Envelope(Base):
    """Tabela Única para registrar dados recebidos."""

    __tablename__ = "devices"

    timestamp = Column(DateTime(timezone=True), primary_key=True, default=func.now())
    attributes = Column(Integer, nullable=True)
    protocol = Column(String, nullable=False)
    src = Column(String, nullable=False)
    dst = Column(String, nullable=False)
    type = Column(String, nullable=False)

    payload = Column(JSON, nullable=False)
