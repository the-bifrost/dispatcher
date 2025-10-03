"""Faz a conexão com o banco de dados."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from ..config import settings


# Cria o motor de conexão com o banco
engine = create_engine(settings.DATABASE_URL)

# Cria uma fábrica de sessões para interagir com o banco
SessionLocal = sessionmaker(autocommmit=False, autoflush=False, bind=engine)

# Classe para os modelos do ORM
Base = declarative_base()
