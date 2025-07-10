"""Handler para abstrair a Conexao/Envio/Recebimento com o broker mqtt

A classe faz a conexão  e reconexão com o broker automaticamente, evitando
problemas com queda da rede.

As funções principais devem seguir o padrão dos handlers da bifrost, os erros são logados
com a lib logging.

Exemplo de uso:

    mqtt = MQTTHadnler("localhost", 1883)
    mqtt.publish("/example/state", "on")
    mqtt.subscribe("/example/state", callback_function)

"""

# TODO - Armazenar tópicos em um json.

import time
import logging

import paho.mqtt.client as mqtt

from utils.envelope import serialize, deserialize

logger = logging.getLogger(__name__)

class MQTTHandler:
    def __init__(self, broker: str, port: int = 1883):
        """Classe para abstrair a Conexao/Envio/Recebimento com o broker mqtt

        Cria uma instância da lib PahoMQTT. Mantemos o padrão de recebimento e envio de dados dos
        handlers do dispatcher.

        A lista de todas os tópicos inscritos é salva em uma variável local, sendo restaurados
        ao reconectar. A classe faz a reconexão automática com o broker em caso de falhas. 

        Args:
            broker: Endereço do broker MQTT.
            port: Porta do broker, por padrão usa a 1883
        """
        self.port   = port
        self.broker = broker
        self.client = mqtt.Client()
        
        self._subscriptions = {}
        self._connected = False
        self._should_reconnect = True

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.client.on_disconnect = self._on_disconnect

        logger.info("Conectando a %s:%s...", self.broker, self.port)
        self._connect()

    def _connect(self):
        """Configura e tenta conexão com o broker mqtt.

        Inicia o loop não travante do mqtt, a primeira tentativa de conexão precisa 
        ser bem sucedida, do contrário encerra o código.

        Não deve ser chamado pelo usuário.
        """
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
            logger.error("Timeout na primeira conexão com %s:%s!", self.broker, self.port)
            exit(1)

    def _on_connect(self, client, userdata, flags, rc):
        """Reinscreve em todos os tópis ao conectar - assíncrono

        É uma função callback para quando a conexão com o broker for bem
        sucedida. Se inscreve novmente em todos os tópicos cadastrados.

        Atualiza a variável interna para permitir envio de mensagens mqtt.
        """
        if rc == 0:
            self._connected = True
            logger.info("Conectado ao Broker com sucesso!")

            for topic in self._subscriptions:
                self.client.subscribe(topic)
        else:
            logger.warning("Falha na conexão com o Broker. Código: %s", rc)

    def _on_disconnect(self, client, userdata, rc):
        """Callback para quando a conexão com broker for encerrada

        Como a reconexão é automática e assíncrona, apenas atualizamos o estado
        interno da conexão para False e logamos
        """
        self._connected = False
        logger.warning("Desconectado de %s:%s. Código: %s", self.broker, self.port, rc)
    
    def _on_message(self, client, userdata, msg):
        """Callback padrão de recebimento de mensagens.

        Aqui são recebidas todas as mensagens dos tópicos inscritos. Para cada tópico
        é conferido se existe uma função callback registrada, se existe, é executada.
        """
        try:
            raw_payload = msg.payload.decode()
            payload = deserialize(raw_payload)
            
            logger.debug(
                "[MQTT::_on_message] Mensagem recebida | Tópico: '%s' | Payload: %s | Raw: %s",
                msg.topic,
                payload,
                raw_payload,
            )
                
            if msg.topic in self._subscriptions:
                self._subscriptions[msg.topic](msg)
                    
        except Exception as e:
            logger.error("[MQTT::_on_message] Erro ao processar mensagem do tópico '%s': %s", msg.topic, e)

    def subscribe(self, topic: str, callback = None):
        """Se inscreve em um tópico e salva função callback

        Todos os tópicos e funções são salvadas internamente. Dessa forma
        podemos re-inscrever nos tópicos em caso de quedas.

        Args:
            topic: String com o tópico que irá se inscrever.
            callback: Uma função que será usada como callback e deve
                esperar "msg".
        """
        self.client.subscribe(topic)
        self._subscriptions[topic] = callback or (lambda x: None)
        logger.info("Inscrito com sucesso no tópico: '%s'", topic)

    def publish(self, topic: str, payload, qos: int = 0, retain: bool = False) -> bool:
        """Publica uma mensagem em um tópico.
        
        É um encapsulamento de publish, com algumas verificações e travas para não
        enviar mensagens quando está offline.

        Args:
            topic: Uma string com o tópico que irá publicar a mensagem.
            payload: As informações que serão publicadas.
            qos: Nível de qos da mensagem (padrão é 0).
            retain: Se a mensagem deve ser retira ou não (padrão é False).

        Returns:
            Em caso de erros ou de mensagens inválidas, retorna False.

            True, em caso de sucesso.
        """
        if not self._connected:
            logger.warning("Tentativa de publicação sem conexão ativa | Tópico: '%s' | Payload: %s", topic, payload)
            return False
        
        try:
            if not isinstance(payload, str):
                payload = serialize(payload)
            
            info = self.client.publish(topic, payload, qos=qos, retain=retain)
            return info.rc == mqtt.MQTT_ERR_SUCCESS

        except Exception as e:
            logger.warning("Erro ao publicar MQTT | Tópico: '%s' | Payload: %s", topic, payload)
            return False

    def handleMessage(self, destination_info: dict, message:dict) -> bool:
        """ Função para lidar com mensagens recebidas pelo Dispatcher
        
        Args:
            destination_info: Dicionário com as informações do destinatário (tópico e protocolo).
            message: Dicionário no padrão de mensagem da Bifrost.

        Returns:
            Bool: Em caso de sucesso, irá retornar True. Se ocorrer algum erro,
                irá retornar False.  
        """
        base_topic = destination_info["topic"].rstrip("/")
        payload = message.get("payload",{})

        if isinstance(payload, dict):
            for key, value in payload.items():
                subtopic = f"{base_topic}/{key}"

                logger.debug("Publicando em tópico: '%s' | Payload: %s", subtopic, payload)
                self.publish(subtopic, value)
        else:
            logger.debug("Publicando em tópico: '%s' | Payload: %s", base_topic, payload)
            self.publish(base_topic, payload)

    def read(self) -> dict | None:
        """Função padrão da bifrost para leitura dos Handlers
        
        Returns:
            None
        """
        # TODO - AINDA NÃO IMPLMENTADA, PRECISA SER USADA COMO CALLBACK DOS SUBSCRIBES
        return None
    
    def close(self):
        """Função padrão da Bifrost para fechar a conexão, um encapsulamento de disconnect()"""
        self.disconnect()

    def disconnect(self):
        """Desativa a reconexão e chama mqtt.disconnect()"""
        self._should_reconnect = False
        self.client.disconnect()