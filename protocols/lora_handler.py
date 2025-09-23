"""Handler para enviar e receber dados LoRa através de uma interface Serial"""

import logging

import serial

from models.devices import Device, LoraDevice
from protocols import BaseHandler
from utils.envelope import Envelope, parse_envelope

logger = logging.getLogger(__name__)


class LoraHandler(BaseHandler):
    def __init__(self, port: str, baudrate: int):
        """Classe para fazer a Conexão/Envio/Recebimento de Dados Seriais."""
        self.port = port
        self.baudrate = baudrate

        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        logger.info("Conectado à porta '%s' @ %dbps", self.port, self.baudrate)
        
    def read(self) -> Envelope | None:
        """Faz a leitura na porta serial, valida e converte dados em um Envelope."""

        if not self.ser or not self.ser.is_open or not self.ser.in_waiting:
            return None
        
        # Lê dados na serial
        raw = self.ser.readline().decode('utf-8', errors='ignore').strip()

        # Filtro mínimo para descartar linhas vazias
        if not raw or len(raw) < 3:  
            return None

        if not (raw.startswith('{') and raw.endswith('}')):
            return None
        
        # Devolve o resultado da conversão em um Envelope
        return parse_envelope(raw)
    
    def write(self, envelope: Envelope, device: Device) -> bool:
        """Recebe um envelope e um dispositivo genérico, converte o envelope em json string e envia para a porta serial."""

        # Verifica se o dispositivo realmente é do tipo que o handler espera.
        if not isinstance(device, LoraDevice):
            logger.error("Handler recebeu um tipo de dispositivo incorreto. Esperado: LoraDevice, Recebido: %s", type(device).__name__)
            return False


        # Converte o Envelope em uma string JSON
        json_envelope = envelope.model_dump_json()

        #Chama a função para fazer o envio
        self._send_string(json_envelope)
        return True

    def _send_string(self, data: str):
        """Converte string em bytes e envia para a porta serial"""

        if not self.ser or not self.ser.is_open:
            logger.error("Porta serial '%s' não está disponível para envio.", self.port)
            return

        try:
            self.ser.write(data.encode('utf-8') + b'\n')
            logger.info("Enviado: '%s' para '%s' @ %dbps - ", data, self.port, self.baudrate)
        except Exception as e:
            logger.error("Falha ao enviar para a porta '%s': %s", self.port, e)

    def close(self):
        """Instancia a função .close() do pySerial"""
        if self.ser and self.ser.is_open:
            self.ser.close()
            logger.info("Conexão serial com '%s' fechada.", self.port)
