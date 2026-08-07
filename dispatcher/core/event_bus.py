"""Barramento de Eventos da Dispatcher, cria listeners e dispara eventos."""

import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable
from typing import Any

_LOGGER = logging.getLogger(__name__)


class EventBus:
    """Barramento de Eventos para ouvir e publicar em tópicos, de forma assíncrona."""

    def __init__(self):
        """Cria uma instância do Barramento de Eventos. Inicializa o dicionário de inscrições em eventos."""
        self._listeners: dict[str, list[Callable]] = defaultdict(list)

    # A inscrição não precisa ser assíncrona por que apenas adiciona uma função no dicionário.
    # A chave do dicionário é o tipo de evento que está sendo inscrito.
    def subscribe(self, event_type: str, callback: Callable):
        """Registra um callback para escutar um tipo de evento."""
        self._listeners[event_type].append(callback)
        _LOGGER.info(
            "Callback %s inscrito no evento '%s'", callback.__name__, event_type
        )

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove um callback previamente registrado para um tipo de evento."""
        try:
            self._listeners[event_type].remove(callback)
            _LOGGER.info(
                "Callback %s desinscrito do evento '%s'", callback.__name__, event_type
            )
        except ValueError:
            _LOGGER.debug(
                "Callback %s não estava inscrito no evento '%s'",
                callback.__name__,
                event_type,
            )

    # A publicação dispara cada callback em uma task independente, para que um
    # ouvinte lento ou travado não atrase os demais nem o próprio publish.
    async def publish(self, event_type: str, data: Any = None) -> None:
        """Dispara um evento para todos os ouvintes, sem aguardar a execução deles."""
        _LOGGER.info("Publicando evento %s com data: %s", event_type, data)

        listeners = self._listeners.get(event_type)

        if not listeners:
            _LOGGER.debug("Nenhum ouvinte para o evento '%s'", event_type)
            return

        for callback in listeners:
            asyncio.create_task(self._run_callback(callback, event_type, data))

    async def _run_callback(
        self, callback: Callable, event_type: str, data: Any
    ) -> None:
        """Executa um callback isolado, registrando erros sem afetar outros ouvintes."""
        try:
            await callback(data)
        except Exception:
            _LOGGER.exception(
                "Erro isolado no callback '%s' para evento '%s'",
                callback.__name__,
                event_type,
            )


# Toda a apliação importa/usa a mesma instância do barramento de eventos.
event_bus = EventBus()
