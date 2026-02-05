"""Script para cadastrar novos dispositivos no banco SQLite da Bifrost."""

import asyncio
import json
import argparse
from pathlib import Path

from dispatcher.core.device_registry import DeviceRegistry
from dispatcher.utils.token import generate_token
from dispatcher.settings import load_configuration

async def register(device_id: str, protocol: str, config_json: str):
    # Carrega as configurações para pegar o caminho do banco
    config_dir = Path("config")
    settings = load_configuration(config_dir / "config.yaml")
    
    # Inicializa o Registry
    registry = DeviceRegistry(
        db_path=config_dir / settings.registry_db_path,
        schema_path=config_dir / settings.registry_db_schema_path
    )
    
    # Gera um novo token único para o dispositivo
    token = generate_token()
    
    try:
        config_dict = json.loads(config_json)
    except json.JSONDecodeError:
        print("Erro: O campo 'config' deve ser um JSON válido. Ex: '{\"address\": \"AA:BB:CC\"}'")
        return

    # Salva no SQLite
    await registry.add_device(
        device_id=device_id,
        protocol=protocol,
        config=config_dict,
        token=token
    )

    print("\n" + "="*40)
    print(f"✅ Dispositivo '{device_id}' cadastrado com sucesso!")
    print(f"🔑 TOKEN: {token}")
    print("="*40)
    print("⚠️ IMPORTANTE: Salve este token. Você precisará dele no código do seu ESP32/ESP8266.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cadastra dispositivos no SQLite da Bifrost")
    parser.add_argument("id", help="ID único do dispositivo (ex: termohigrometro-01)")
    parser.add_argument("protocol", help="Protocolo (lora, espnow, mqtt)")
    parser.add_argument("config", help="JSON com configs específicas (ex: '{\"address\": \"MAC\"}')")

    args = parser.parse_args()
    asyncio.run(register(args.id, args.protocol, args.config))