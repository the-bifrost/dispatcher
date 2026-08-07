"""Classe base para os nós do Flow Engine da Bifrost."""

import logging

_LOGGER = logging.getLogger(__name__)


class Node:
    """Classe base de um nó do flow.

    Cada nó recebe uma mensagem, processa, e repassa o resultado (se houver)
    para seus nós de saída. Mensagens têm o formato {"envelope": Envelope, "device": Device},
    o mesmo usado pelo evento Device.VALIDATED.
    """

    def __init__(self, node_id: str, config: dict, registry=None):
        self.id = node_id
        self.config = config
        self.registry = registry
        self.outputs: list[Node] = []

    def add_output(self, node: "Node"):
        """Conecta este nó a um nó de saída (wire)."""
        self.outputs.append(node)

    async def receive(self, message: dict):
        """Processa a mensagem e repassa o resultado para os nós de saída."""
        result = await self.process(message)

        if result is None:
            return

        for output in self.outputs:
            await output.receive(result)

    async def process(self, message: dict) -> dict | None:
        """Processa a mensagem. Retorna None para interromper o flow neste ponto."""
        raise NotImplementedError
