# Bifrost Dispatcher

A Dispatcher é o *núcleo de roteamento da central* Bifrost, responsável por receber mensagens de múltiplos protocolos, identificar seus destinos e repassá-las corretamente entre os dispositivos conectados.

## Formato de comunicação padrão.

Para garantir a compatibilidade entre protocolos, as mensagens são enviadas dentro de um **"envelope comum"** no formato JSON.

```json
{
  "v": 1,
  "src": "source/fonte/sensor",
  "dst": "destino",
  "protocol": "device_protocol",
  "type": "tipo-da-mensagem",
  "ts": 1686026400,
  "payload": {}
}
```

# Arquitetura do Software

Event-Driven Aplication (EDA)

## Tutoriais

- [Liberar portas UART do Raspberry Pi 5](/docs/habilitando-uart-raspberry.md)

## Funcionalidades

- 🔌 Inicializa múltiplos protocolos de comunicação.

- 📦 Despacha mensagens entre dispositivos de acordo com o protocolo.

- 🧾 Gerencia um registro dinâmico de dispositivos.

- 🔁 Executa loop contínuo de leitura e roteamento.

- 🛑 Reconecta com o broker MQTT em caso de falhas.

## Para fazer

- [ ] Trabalhar com Assíncronicidade
- [ ] Implementar Arquitetura EDA
