"""Faz a conexão da dispatcher com o InfluxDB"""

import logging
import os
from dotenv import load_dotenv

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

logger = logging.getLogger(__name__)

# Carrega as configurações do .env na raiz do projeto
load_dotenv()

# Acessa as variáveis configuradas Pegando o token pelas variáveis do sistema.
token = os.environ.get("INFLUXDB_TOKEN")
url = os.environ.get("INFLUXDB_URL")
org = os.environ.get("INFLUXDB_ORG")
bucket = os.environ.get("INFLUXDB_BUCKET")

# Inicializando o client do InfluxDB
client = InfluxDBClient(url=url, token=token)

# Inicia a API de escrita usando client.
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_data(point_dict: dict):
    """Usa a API do Influx para escrever no database"""
    point = Point.from_dict(point_dict)
    write_api.write(bucket=bucket, org=org, record=point)
    logger.debug("Escrevendo dados no InfluxDB: %s", point_dict)

def envelope_to_point_dict(message: dict, measurement: str) -> dict:
    point_dict = {}

    point_dict["measurement"] = measurement
    point_dict["fields"] = message.get("payload")

    point_dict["tags"] = {
        "src": message.get("src"),
        "protocol": message.get("protocol"),
        "type": message.get("type"),
    }

    return point_dict 

def close_write_api():
    write_api.close()


def main():
    """Debug"""

    import random
    import time

    for i in range(10):
        message = {
            "v": 1,
            "src": "dht-esp32",
            "dst": "destino",
            "protocol": "espnow",
            "type": "data",
            "ts": 1686026400,
            "payload": {
                "temperature": random.randint(20, 30),
                "humidity": random.randint(60, 80)
            }
        }

        write_data(envelope_to_point_dict(message=message, measurement="Testing"))
        time.sleep(0.1)


    close_write_api()

if __name__ == "__main__":
    """Debug"""
    main()