"""Faz a conexão da dispatcher com o InfluxDB"""

import logging
import os
from dotenv import load_dotenv

from influxdb_client.client.influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS
from influxdb_client.rest import ApiException

from utils.envelope import Envelope

logger = logging.getLogger(__name__)

# Carrega as configurações do .env na raiz do projeto
load_dotenv()

# Acessa as variáveis configuradas Pegando o token pelas variáveis do sistema.
token = os.environ.get("INFLUXDB_TOKEN", "your_token_here")
url = os.environ.get("INFLUXDB_URL", "localhost:8086")
org = os.environ.get("INFLUXDB_ORG", "Bifrost")
bucket = os.environ.get("INFLUXDB_BUCKET", "Dispatch")

# Inicializando o client do InfluxDB
client = InfluxDBClient(url=url, token=token)

# Inicia a API de escrita usando client.
write_api = client.write_api(write_options=SYNCHRONOUS)

def write_data(point_dict: dict):
    """Usa a API do Influx para escrever no database"""
    point = Point.from_dict(point_dict)

    try:
        write_api.write(bucket=bucket, org=org, record=point)
        logger.debug("Escreveu dados no InfluxDB: %s", point_dict)
    except ApiException as e:
        logger.error("Erro ao escrever dados no InfluxDB: %s", e.message)

def envelope_to_point_dict(message: Envelope, measurement: str) -> dict:
    point_dict = {}

    point_dict["measurement"] = measurement
    point_dict["fields"] = message.payload

    point_dict["tags"] = {
        "src": message.src,
        "protocol": message.protocol,
        "type": message.type
    }

    return point_dict 

def close_write_api():
    write_api.close()
