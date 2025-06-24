import json
import time

def make_envelope(src: str, dst: str, payload, msg_type="state", version=1) -> dict:
    return {
        "v": version,
        "src": src,
        "dst": dst,
        "type": msg_type,
        "ts": int(time.time()),
        "payload": payload
    }

def serialize(env: dict) -> str:
    return json.dumps(env)

# deserialize()
#   - Espera uma string -> raw
#   - Tenta carregar ela como JSON
#   - Se Sucesso -> Retorna um dicionário.
def deserialize(raw: str) -> dict | None:
    try:
        return json.loads(raw)
    
    # Se der algum erro, vai printar e retornar nulo.
    except json.JSONDecodeError as e:
        print(f"[JSON] Conversão inválida (erro: {e}): {raw[:50]}...")
        return None
    except Exception as e:
        print(f"[JSON] Erro inesperado: {e}")
        return None