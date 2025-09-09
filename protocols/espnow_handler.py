"""Handler para enviar e receber dados Seriais"""

import logging

import serial

from models.devices import Device, EspNowDevice
from protocols import BaseHandler
from utils.envelope import Envelope, parse_envelope

logger = logging.getLogger(__name__)


class EspNowHandler(BaseHandler):
    def __init__(self, port: str, baudrate: int):
        """Classe para fazer a Conexão/Envio/Recebimento de Dados Seriais."""
        self.port = port
        self.baudrate = baudrate

        self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
        logger.info("Conectado à porta '%s' @ %dbps", self.port, self.baudrate)
        
    def read(self) -> Envelope | None:
        """Faz a leitura na porta serial, valida e converte dados em um Envelope."""

        if not self.ser.in_waiting:
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
        if not isinstance(device, EspNowDevice):
            logger.error("Handler recebeu um tipo de dispositivo incorreto. Esperado: EspNowDevice, Recebido: %s", type(device).__name__)
            return False

        # Faz um cópia local do envelope
        envelope_to_send = envelope.model_copy(deep=True)

        # Troca o id do destino para o endereço físico do esp.
        envelope_to_send.dst = device.address

        # Converte o Envelope em uma string JSON
        json_envelope = envelope.model_dump_json()

        #Chama a função para fazer o envio
        self._send_string(json_envelope)
        return True

    def _send_string(self, data: str):
        """Converte string em bytes e envia para a porta serial"""

        try:
            self.ser.write(data.encode('utf-8') + b'\n')
            logger.info("Enviado: '%s' para '%s' @ %dbps - ", data, self.port, self.baudrate)
        except Exception as e:
            logger.error("Falha ao enviar para a porta '%s': %s", self.port, e)

    def close(self):
        """Instancia a função .close() do pySerial"""
        self.ser.close = self.close
