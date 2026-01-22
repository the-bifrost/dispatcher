# Bifrost Dispatcher

A Dispatcher é o *núcleo de roteamento da central* Bifrost, responsável por receber mensagens de múltiplos protocolos, identificar seus destinos e repassá-las corretamente entre os dispositivos conectados.

## Envelope de comunicação padrão.

Para garantir a compatibilidade entre protocolos, as mensagens são enviadas dentro de um **"envelope comum"** no formato JSON.

```json
{
  "v": 1,
  "src": "example_kitchen_sensor",
  "dst": "destino",
  "protocol": "device_protocol",
  "type": "tipo-da-mensagem",
  "ts": 1686026400,
  "payload": {}
}
```

## Funcionalidades

- ▶️ Inicialização dinâmica de múltiplos protocolos de comunicação.

- 📦 Despacha mensagens entre dispositivos de diferentes protocolos.

- 🧾 Gerencia e armazena registro de dispositivos.

- 🔁 Executa loop assíncrono para leitura e roteamento.