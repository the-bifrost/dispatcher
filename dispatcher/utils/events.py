"""Centraliza todos os tópicos de eventos do sistema."""


class Events:
    """Classe Global de Eventos."""

    class Protocol:
        """Eventos de entrada/saída bruta de dados."""

        RECEIVED = "protocol.message_received"
        SEND_PREFIX = "protocol.send_to."

    class Device:
        """Eventos da camada de negócio/dispositivos."""

        VALIDATED = "device.message_validated"
        UNKNOWN = "device.unknown"
        STATE_CHANGED = "device.state_changed"
