"""Barramento de Eventos da Dispatcher, cria listeners e dispara eventos."""

import asyncio
import logging
from collections import defaultdict
from typing import Callable, Any


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
        _LOGGER.info("Callback %s inscrito no evento '%s'", callback.__name__, event_type)

    # A publicação de novos eventos é assíncrona pois a cada publicação é necessário percorrer
    # toda a lista de _listeners.
    #
    # Algumas otimizações podem ser feitas para saber se realmente é necessário publciar ou não.
    async def publish(self, event_type: str, data: Any = None) -> None:
        """Dispara um evento para todos os ouvintes."""
        _LOGGER.info("Publicando evento %s com data: %s", event_type, data)

        if event_type not in self._listeners:
            _LOGGER.debug("Nenhum ouvinte para o evento '%s'", event_type)
            return
        
        tasks = []

        for callback in self._listeners[event_type]:
            tasks.append(callback(data))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for callback, result in zip(self._listeners[event_type], results):
           if isinstance(result, Exception):
                _LOGGER.error("Erro no disparo de evento no callback '%s' para evento '%s': %s", callback.__name__, event_type, result)


# Toda a apliação importa/usa a mesma instância do barramento de eventos.
event_bus = EventBus()
