from utils.envelope import serialize, deserialize
import paho.mqtt.client as mqtt
import time

# MQTTHandler
#   - Cria uma instância da classe do MQTT
#   - Usamos ela para abstrair a conexão com o Broker e envio/recebimento de mensagens.
#   - Realizamos tratamento e log dos erros.
class MQTTHandler:
    def __init__(self, broker, port):
        self.port   = port
        self.broker = broker
        self.client = mqtt.Client()
        
        self._subscriptions = {}
        self._connected = False
        self._should_reconnect = True

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        print(f"[MQTT] Conectando a {self.broker}:{self.port}...")
        self._connect()

    # _connect()
    #   - Faz as configurações para reconectar e usar funções assíncronas
    #   - Inicia o loop não-travante do mqtt
    #   - Tenta conectar com o broker
    #   - Retorna erros e encerra, se a primeira conexão não for bem sucedida.
    def _connect(self):
        try:
            self.client.reconnect_delay_set(min_delay=1, max_delay=60)
            self.client.connect_async(self.broker, self.port)
            self.client.loop_start()

            for _ in range(10):
                if self._connected:
                    return True
                time.sleep(0.5)
            raise Exception("Timeout na Conexão")

        except Exception as e:
            print(f"[MQTT] Erro na conexão: {e}")
            exit(1)    

    # _on_connect()
    #   - Callback para quando a conexão com o broker for bem sucedida.
    #   - Se inscreve novamente em todos os tópicos cadastrados.
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"[MQTT] Conectado com sucesso!")

            # Restaurando inscrições após reconexão
            for topic in self._subscriptions:
                self.client.subscribe(topic)
        else:
            print(f"[MQTT] Falha na conexão. Código: {rc}")

    # _on_disconnect()
    #   - Callback para quando a conexão com o broker for encerrada, por qualquer motivo.
    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        print(f"[MQTT] Desconectado. Código: {rc}")
    
    # _on_message()
    #   - Callback para todas as mensagens recebidas nos tópicos inscritos. 
    # Callback padrão para mensagens recebidas
    def _on_message(self, client, userdata, msg):
            try:
                payload = deserialize(msg.payload.decode())
                print(f"[MQTT] Mensagem recebida - Tópico: {msg.topic} | Payload: {payload}")
                
                # Executa callback, caso existir
                if msg.topic in self._subscriptions:
                    self._subscriptions[msg.topic](msg)
                    
            except Exception as e:
                print(f"[MQTT] Erro ao processar mensagem: {e}")

    # subscribe()
    #   - Se inscreve no tópico passado.
    #   - Salva o tópico em _subscriptions para reconectar caso a conexão cair
    #   - Caso for passada uma função callback, cadastra ela.
    def subscribe(self, topic, callback=None):
        self.client.subscribe(topic)
        self._subscriptions[topic] = callback or (lambda x: None)
        print(f"[MQTT] Inscrito no tópico: {topic}")

    # publish()
    #   - Faz o encapsulamento de publish()
    #   - Se certifica de que a payload é de fato uma string
    def publish(self, topic, payload, qos=0, retain=False):
        if not self._connected:
            print("[MQTT] Aviso: Tentando publicar sem conexão ativa")
            return False
        
        try:
            if not isinstance(payload, str):
                payload = serialize(payload)
            
            info =self.client.publish(topic, payload, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS

        except Exception as e:
            print(f"[MQTT] Erro na publicação: {e}")
            return False

    # handleMessage()
    #   - Recebe um dicionário com as infomações do destinatário.
    #   - Das informações do destinatário, retira o tópico.
    #   - Salva a payload recebida pelo dicionário message.
    def handleMessage(self, destination_info, message):
        base_topic = destination_info["topic"].rstrip("/")
        payload = message.get("payload",{})

        if isinstance(payload, dict):
            for key, value in payload.items():
                subtopic = f"{base_topic}/{key}"

                print(f"[MQTT] Sub-Tópico: {subtopic} → {value}")
                self.publish(subtopic, value)
        else:
            print(f"[MQTT] Tópico: {base_topic} → Payload: {payload}")
            self.publish(base_topic, payload)

    # read()
    #   - Função padrão para leitura dos Handlers
    #   - AINDA NÃO IMPLMENTADA, PRECISA SER USADA COMO CALLBACK DOS SUBSCRIBES
    def read(self) -> dict | None:
        return None
    
    # close()
    #   - Função padrão dos Handlers
    #   - Instancia 
    def close(self):
        self.disconnect()

    # disconnect()
    # Define a reconexão como falsa, 
    # Desconecta do Broker 
    def disconnect(self):
        self._should_reconnect = False
        self.client.disconnect()