"""Handler para abstrair a Conexao/Envio/Recebimento com dispositivos

A classe estabelece a conexão serial com as centrais da Bifrost, as funções 
seguem o padrão com read(), send(), handleMessage() e close(). 

Exemplo de uso:

    ser = SerialHandler("/dev/ttyUSB0")
    data = ser.read()

    if data is not None:
        print(data)

"""

import logging

import serial

from utils.envelope import deserialize, serialize, make_envelope

logger = logging.getLogger(__name__)

class SerialHandler:
    def __init__(self, port: str, baudrate: int):
        """ Classe para abstrair a Conexão/Envio/Recebimento de Dados Seriais

        Cria uma instância da lib pySerial. Mantemos o padrão de recebimento e 
        envio de dados dos handlers do dispatcher.
        
        Args:
            port: porta que será usada para tentar conectar Serial
            baudrate: velocidade da transmissão de dados
        """
        self.port = port
        self.baudrate = baudrate

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.ser.flushInput()
            logger.info("Conectado à porta '%s' @ %dbps", self.port, self.baudrate)
        except Exception as e:
            logger.error("Não foi possível abrir '%s': %s", self.port, e)
            exit(1)
        
    def close(self):
        """Instancia a função .close() do pySerial"""
        self.ser.close = self.close

    def read(self) -> dict | None:
        """ Faz a leitura e filtragem de dados na porta conectada.

        Faz a leitura dos dados até que receba uma quebra de linha. Ignora as sujeiras
        recebidas. Todas as mensagens são convertidas em dicionário.

        Returns:
            dict: Retorna um dicionário com uma mensagem bifrost válida
        """
        if not self.ser.in_waiting:
            return None
        
        # Tenta ler até encontrar uma quebra de linha ou limite de tamanho
        raw = self.ser.readline().decode('utf-8', errors='ignore').strip()

        # Descarta qualquer lixo que entrar na serial -> Mensagem mínima válida: {}
        if not raw or len(raw) < 3:  
            return None

        if not (raw.startswith('{') and raw.endswith('}')):
            return None
        
        # Tenta converter em um dicionário.
        # Se erro, retorna Nulo.
        # Se sucesso, retorna dicionário.
        try:
            data = deserialize(raw)
            
            if not isinstance(data, dict):
                return None
                
            # Verifica campos obrigatórios
            if 'src' not in data or 'dst' not in data:
                logger.debug("%s - JSON recebido com estrutura incompleta: %s", self.port, raw)
                return None
                
            return data
        except Exception as e:
            logger.warning("%s - Erro inesperado: %s", self.port, raw)
            return None
    
    def send(self, string: str):
        """Envia uma string para a porta serial conectada
        
        Args:
            string: Uma string com os dados que serão enviados
        """
        self.ser.write(string.encode('utf-8') + b'\n')
        logger.info("Enviado: '%s' para '%s' @ %dbps - ", string, self.port, self.baudrate)

    def handleMessage(self, destination_info: dict, message: dict):
        """Faz o tratamento dos dados recebidos para enviar via send()

        É uma implementação padrão dos Handlers da Bifrost.

        Args:
            destination_info: Um dicionário com as infomações do destinatário.
            message: Um dicionário com a mensagem que deve ser redirecionada.
        """
        source = message["src"]
        destination = destination_info["address"]
        payload = message["payload"]

        # Envelopando e enviando
        message = make_envelope(source, destination, payload)
        sendMessage = serialize(message)
        self.send("SEND:" + sendMessage)

