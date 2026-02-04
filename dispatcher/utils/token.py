""""""

import bcrypt
import secrets

# 1. Geração (Simulando o momento da criação)
token_real = secrets.token_urlsafe(32)
print(f"Guarde este token, não vamos mostrá-lo novamente: {token_real}")

# 2. Armazenamento (Hashing)
# O bcrypt lida com o "salt" automaticamente para você
token_bytes = token_real.encode('utf-8')
token_hash = bcrypt.hashpw(token_bytes, bcrypt.gensalt())

# Salve 'token_hash' no seu banco de dados (Postgres, MySQL, etc.)
print(f"O que vai para o banco: {token_hash}")

# ---------------------------------------------------------

# 3. Verificação (Quando o usuário tenta usar o token)
token_enviado_pelo_usuario = token_real # Simulando o input
token_enviado_bytes = token_enviado_pelo_usuario.encode('utf-8')

# A função checkpw faz o hash do input e compara com o hash salvo
if bcrypt.checkpw(token_enviado_bytes, token_hash):
    print("Acesso Permitido!")
else:
    print("Token Inválido.")