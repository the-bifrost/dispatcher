"""Barramento de Eventos da Dispatcher, cria listeners e dispara eventos."""

import logging
from collections import defaultdict
from typing import Callable, Any


_LOGGER = logging.getLogger(__name__)


class EventBus:
    def __init__(self) -> None:
        """Cria um dicionário de inscrições em eventos."""
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

        def subscribe(self, event_type: str, callback: Callable):
            """Registra um callback para escutar um tipo de evento."""
            self._listeners[event_type].append(callback)
            _LOGGER.info("Callback %s inscrito no evento '%s'", callback.__name__, event_type)

        def publish(self, event_type: str, data: Any = None):
            """Dispara um evento para todos os ouvintes."""
            _LOGGER.info("Publicando evento %s com data: %s", event_type, data)

            for callback in self._listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    _LOGGER.error("Error no disparo de evento para %s: %s", event_type, e)

# Fazemos uma insância para toda a aplicação.
event_bus = EventBus()

