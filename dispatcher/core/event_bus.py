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
        """Cria uma instância do EventBus e inicializa o dict de inscrições e rastreio de tasks"""
        self._listeners: dict[str, list[Callable]] = defaultdict(list)
        self._background_tasks: set[asyncio.Task] = set()

    def _get_callback_name(self, callback: Callable) -> str:
        """Obtém o nome do callback com segurança, evitando AttributeError se não tiver __name__."""
        return getattr(callback, "__name__", str(callback))

    def subscribe(self, event_type: str, callback: Callable):
        """Registra um callback para escutar um tipo de evento."""
        self._listeners[event_type].append(callback)
        _LOGGER.info(
            "Callback %s inscrito no evento '%s'", self._get_callback_name(callback), event_type
        )

    def unsubscribe(self, event_type: str, callback: Callable):
        """Remove um callback previamente registrado para um tipo de evento."""
        try:
            self._listeners[event_type].remove(callback)
            _LOGGER.info(
                "Callback %s desinscrito do evento '%s'",
                self._get_callback_name(callback),
                event_type,
            )
        except ValueError:
            _LOGGER.debug(
                "Callback %s não estava inscrito no evento '%s'",
                self._get_callback_name(callback),
                event_type,
            )

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Dispara um evento para todos os ouvintes, sem aguardar a execução deles."""
        _LOGGER.debug("Publicando evento %s com data: %s", event_type, data)

        listeners = self._listeners.get(event_type)

        if not listeners:
            _LOGGER.debug("Nenhum ouvinte para o evento '%s'", event_type)
            return

        for callback in listeners:
            task = asyncio.create_task(self._run_callback(callback, event_type, data))
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

    def publish_soon(self, event_type: str, data: Any = None) -> None:
        """
        Gatilho síncrono para publicar eventos de locais que não são sync.
        Enfileira a task de forma segura e rastreada.
        """
        task = asyncio.create_task(self.publish(event_type=event_type, data=data))
        task.add_done_callback(self._background_tasks.discard)

    async def wait_idle(self):
        """Aguarda a conclusão das tasks em background."""
        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

    async def _run_callback(self, callback: Callable, event_type: str, data: Any) -> None:
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
