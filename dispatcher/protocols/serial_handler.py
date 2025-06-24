import serial
from utils.envelope import deserialize, serialize, make_envelope

# SerialHandler
#   - Faz a conexão com as unidades dos protocolos
#   - Em caso de erro, encerra o código.
#   - Instancia as funções base do serial
#   - Manipula os dados recebidos do dispatcher para enviar/receber mensagens
class SerialHandler:
    def __init__(self, port, baudrate):
        self.port = port
        self.baudrate = baudrate

        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=1)
            self.ser.flushInput()
        except Exception as e:
            print(f"[SERIAL] Não foi possível abrir {self.port}: {e}")
            exit(1)
        
        print(f"[SERIAL] Conectado em {self.port} @ {self.baudrate}bps")

    # close()
    #   - instância do .close() original para encapsular a classe.
    def close(self):
        self.ser.close = self.close

    # read()
    #   - Tenta fazer a leitura até que receba uma quebra de linha
    #   - Filtra possíveis sujeiras recebidas (mensagens curtas ou fora do padrão JSON)
    #   - Chama deserialize para converter em dicionário
    #   - Se erro, retorna None
    #   - Se sucesso, retorna o dicionário da leitura.
    def read(self) -> dict | None:
        if not self.ser.in_waiting:
            return None
        
        # Tenta ler até encontrar uma quebra de linha ou limite de tamanho
        raw = self.ser.readline().decode('utf-8', errors='ignore').strip()

        # Descarta qualquer lixo que entrar na serial -> Mensagem mínima válida: {}
        if not raw or len(raw) < 3:  
            return None

        # Verifica se parece ser um JSON (começa com { e termina com })
        if not (raw.startswith('{') and raw.endswith('}')):
            #print(f"[SERIAL] Formato inválido (não é JSON): {raw[:50]}...")
            return None
        
        # Tenta transformar em um dicionário, se erro, retorna Nulo.
        try:
            data = deserialize(raw)
            
            # Validação adicional da estrutura esperada
            if not isinstance(data, dict):
                print(f"[SERIAL] JSON não é um dicionário: {raw[:50]}...")
                return None
                
            # Verifica campos obrigatórios (opcional)
            if 'src' not in data or 'dst' not in data:
                print(f"[SERIAL] Estrutura incompleta: {raw[:50]}...")
                return None
                
            return data
        except Exception as e:
            print(f"[SERIAL] Erro inesperado: {e}")
        return None
    
    # send()
    #   - Encapsulamento da função de enviar.
    #   - Printa o que foi enviado.
    def send(self, string: str):
        self.ser.write(string.encode('utf-8') + b'\n')
        print(f"[SERIAL] Enviado: {string}")

    # handleMessage()
    #    - Recebe um dicionário
    #    - 
    def handleMessage(self, destination_info: dict, message: dict):
        source = message["src"]
        destination = destination_info["address"]
        payload = message["payload"]

        # Envelopando e enviando
        message = make_envelope(source, destination, payload)
        sendMessage = serialize(message)
        self.send("SEND:" + sendMessage)

