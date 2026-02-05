"""Utilitário padrão para lidar com tokens da bifrost."""

import logging
import secrets

import bcrypt


_LOGGER = logging.getLogger(__name__)


def generate_token(nbytes:int = 16) -> str:
    """Gera um token para autenticação dos dispositivos e retorna em string hexadecimal."""
    return secrets.token_bytes(nbytes).hex()

def hash_token(bytes_token: str) -> bytes:
    """Gera o hash para salvar no banco."""
    return bcrypt.hashpw(bytes_token.encode(), bcrypt.gensalt())

def verify_token(bytes_token: str, hashed_token: bytes) -> bool:
    """Compara um token e uma hash de token. Retorna True se iguais."""

    if isinstance(hashed_token, str):
            hashed_token = hashed_token.encode('utf-8')

    try:
        return bcrypt.checkpw(bytes_token.encode(), hashed_token)
    except Exception as e:
        _LOGGER.error("Erro na verificação do bcrypt: %s", e)
        return False
