"""Utilitário padrão para lidar com tokens da bifrost."""

import logging
import secrets

import bcrypt


_LOGGER = logging.getLogger(__name__)


def generate_token(nbytes:int = 16) -> bytes:
    """Gera um token para autenticação dos dispositivos."""
    return secrets.token_bytes(nbytes=nbytes)

def hash_token(bytes_token: bytes) -> bytes:
    """Gera o hash para salvar no banco."""
    return bcrypt.hashpw(bytes_token.hex().encode(), bcrypt.gensalt())

def verify_token(bytes_token: bytes, hashed_token: bytes) -> bool:
    """Compara um token e uma hash de token. Retorna True se iguais."""
    if bcrypt.checkpw(bytes_token, hashed_token):
        return True
    
    return False