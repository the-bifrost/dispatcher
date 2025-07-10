<!--
<img src="https://oyster.ignimgs.com/mediawiki/apis.ign.com/marvel-studios-cinematic-universe/7/7e/Bifrost1.jpg" style="width:100%; height:200px; object-fit: cover;">

<hr>
-->
<div align="center">
  <a href="https://github.com/thalesgmartins/bifrost">
    <img src="https://miro.medium.com/v2/resize:fit:798/1*FrYsyFjTh5UsAGidVZmTdw.png" alt="Logo" width="100" height="100">
  </a>

<h3 align="center" style="font-size:32px;">Bifrost</h3>

  <p align="center" style="font-size:20px;">
    Gateway de Protoclos Wireless!
    <br />
    <a href="https://github.com/thalesgmartins/bifrost"><strong>Ver mais »</strong></a>
    <br>
    <hr>
    <img style="height:52px;" src="https://skillicons.dev/icons?i=python,docker,arduino,raspberrypi&theme=dark" />
    <hr>
</div>

<h3 style="font-size:32px">Introdução</h3>
<p>
  Uma <strong>central de comunicação inteligente</strong> que conecta múltiplos dispositivos usando diversas tecnologias sem fio, como <strong>ESP-NOW</strong>, <strong>LoRa</strong>, <strong>MQTT</strong> e futuramente <strong>Zigbee</strong>. O objetivo é permitir o envio e recebimento de dados entre sensores, atuadores e a central de forma eficiente, roteando as mensagens para os respectivos destinos.
</p>

<hr>

<h3 style="font-size:24px;">Raspberry Pi <img style="height:24px;" src="https://skillicons.dev/icons?i=raspberrypi&theme=dark" /> como Central (Dispatcher)</h3>
<ul>
  <li>O <strong>Raspberry Pi 4B</strong> atua como a <strong>central principal (dispatcher)</strong> da rede.</li>
  <li>Ele é responsável por:
    <ul>
      <li>Receber as mensagens de vários gateways e dispositivos;</li>
      <li>Armazenar dados, gerenciar dispositivos e tópicos (MQTT);</li>
      <li>Decidir qual protocolo usar para enviar cada mensagem;</li>
      <li>Fazer a ponte entre protocolos diferentes (exemplo: receber via ESP-NOW e retransmitir via MQTT).</li>
    </ul>
  </li>
</ul>

<h3>Vantagens do Raspberry Pi</i> na central </h3>
<ul>
  <li>Processamento mais robusto e flexível do que ESP32s;</li>
  <li>Capacidade de rodar scripts Python para lógica e roteamento;</li>
  <li>Pode hospedar banco de dados local e broker MQTT (ex: Mosquitto);</li>
  <li>Interface com múltiplas interfaces físicas (UART, SPI, Ethernet, Wi-Fi).</li>
</ul>
<hr>
  <h3 style="font-size:32px;">Protocolos Envolvidos</h3>
  <div style="">
    <div>
      <h3>ESP-NOW <img style="height:24px; justify-content:center;" src="https://gndtovcc.home.blog/wp-content/uploads/2020/04/2.1-1.png?w=640"></h3>
      <ul>
        <li>Comunicação Wi-Fi ponto a ponto, rápida e com baixo consumo;</li>
        <li>Ideal para troca direta entre ESP32s sem passar por roteador.</li>
      </ul>
    </div>
    <div>
      <h3>LoRa <img style="height:24px; justify-content:center;" src="https://ucarecdn.com/8a5b76a7-5969-43c9-b60e-de8d62824d09/lora%20logo%20white%20transparent.svg" > </img></h3>
      <ul>
        <li>Comunicação de longo alcance e baixo consumo;</li>
        <li>Útil para sensores remotos que não têm Wi-Fi.</li>
      </ul>
    </div>
    <div>
      <h3>MQTT <img style="height:24px; justify-content:center;" src="https://github.com/mqtt/mqttorg-graphics/blob/master/png/mqtt-icon-transparent.png?raw=true"> </h3>
      <ul>
        <li>Protocolo leve de mensagens para IoT, baseado em tópicos;</li>
        <li>Rodado em broker no Raspberry Pi;</li>
        <li>Excelente para comunicação em redes IP, controle remoto e armazenamento em nuvem.</li>
      </ul>
    </div>
    <div>
      <h3>Zigbee (Futuramente) <img style="height:24px; justify-content:center;" src="https://img.icons8.com/?size=512&id=80168&format=png"> </h3>
      <ul>
        <li>Protocolo mesh para IoT;</li>
        <li>Potencial para maior escalabilidade e roteamento dinâmico.</li>
      </ul>
    </div>
  </div>
<hr>
<h3 style="font-size:24px;">Formato de Comunicação: JSON <img src="https://static-00.iconduck.com/assets.00/file-type-json-icon-2044x2048-7l7nm0fy.png" style="height:24px;"> Padronizado  </h3>
<p>Para garantir interoperabilidade, as mensagens são enviadas dentro de um <strong>"envelope comum"</strong> no formato JSON.</p>
<h3>Estrutura Básica do JSON:</h3>

```json
{
  "v": 1, //versao do codigo
  "src": "source/fonte/sensor", //origem da mensagem
  "dst": "destino", //destino da mensangem
  "type": "tipo-da-mensagem", //tipo
  "ts": 1686026400, //timestamp
  "payload": {
    //payload da mensagem
    //dados específicos da mensagem
  }
}
```

<hr>
<h3 style="font-size:24px;">Funcionalidades:</h3>
<ul>
  <li>Comunicação ESP-NOW entre ESP8266;</li>
  <li>Comunicação UART entre ESP8266 e Raspberry Pi 4;</li>
  <li>Liberação de UART's "Extras" do Raspberry Pi 4 (Possível utilização de até 5 RX & TX);</li>
  <li>Docker MQTT Broker;</li>
  <li>Comunicação MQTT com o Broker;</li>
  <li>Filtro de mensagens da payload;</li>
  <li>MQTT Explorer para controle da comunicação MQTT e debug;</li>
  <li>Acesso externo ao MQTT Explorer via Cloudflared;</li>
</ul>
<hr>
<h3 style="font-size:24px;">Tutoriais</h3>
<ul>
  <li style="text-decoration: none;"><a href="dispatcher/UART-Ports.md">Liberando portas UART »</a></li>
</ul>
<hr>
<h3 style="font-size:24px; margin-top: 24px;">Metas do Desenvolvimento</h3>

<details style="margin-bottom: 12px;">
  <summary style="font-size:18px; cursor:pointer;"><strong> Protocolos</strong></summary>
  <ul style="margin-top: 8px;">
    <li><input type="checkbox" disabled> Implementar suporte completo ao <strong>ESP-NOW</strong></li>
    <li><input type="checkbox" disabled> Estabelecer comunicação estável via <strong>LoRa</strong></li>
    <li><input type="checkbox" disabled> Integrar <strong>MQTT</strong> com o broker e tópicos dinâmicos</li>
    <li><input type="checkbox" disabled> Iniciar testes com <strong>Zigbee</strong></li>
  </ul>
</details>

<details style="margin-bottom: 12px;">
  <summary style="font-size:18px; cursor:pointer;"><strong> Funcionalidades</strong></summary>
  <ul style="margin-top: 8px;">
    <li><input type="checkbox" disabled> Biblioteca própria da Bifrost</li>
    <li><input type="checkbox" disabled> Interface web para monitoramento</li>
    <li><input type="checkbox" disabled> Filtro de payloads por tipo e origem</li>
    <li><input type="checkbox" disabled> Roteamento inteligente entre protocolos</li>
    <li><input type="checkbox" disabled> MQTT Explorer para melhor Debug</li>
  </ul>
</details>

<details style="margin-bottom: 12px;">
  <summary style="font-size:18px; cursor:pointer;"><strong> Hardware</strong></summary>
  <ul style="margin-top: 8px;">
    <li><input type="checkbox" disabled> Instalar múltiplos gateways físicos</li>
    <li><input type="checkbox" disabled> Habilitar até 5 UARTs no Raspberry Pi 4</li>
    <li><input type="checkbox" disabled> Testar estabilidade de alimentação dos módulos</li>
    <li><input type="checkbox" disabled> Garantir isolamento entre interfaces físicas</li>
  </ul>
</details>
