"""Flow Runner. Lê automations.json, instancia os nós e executa o pipeline configurado."""

import json
import logging
from pathlib import Path

from ..core.device_registry import DeviceRegistry
from ..core.event_bus import EventBus
from ..utils.events import Events
from .node import Node
from .nodes import NODE_REGISTRY, InputNode

_LOGGER = logging.getLogger(__name__)


class FlowRunner:
    def __init__(self, flows_path: Path, registry: DeviceRegistry, event_bus: EventBus):
        self.flows_path = flows_path
        self.registry = registry
        self._nodes: dict[str, Node] = {}
        self._input_nodes: list[InputNode] = []
        self.event_bus = event_bus

    async def start(self):
        """Carrega o automations.json e conecta os nós pela primeira vez."""
        await self.reload()

    async def reload(self):
        """Recarrega o flow a partir do disco, substituindo o anterior sem derrubar a Bifrost."""
        self._teardown()

        if not self.flows_path.exists():
            _LOGGER.warning("Arquivo de automações não encontrado: %s", self.flows_path)
            return

        try:
            data = json.loads(self.flows_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            _LOGGER.error("automations.json inválido: %s", e)
            return

        self._build(data)
        _LOGGER.info(
            "Flow recarregado: %d nó(s), %d conexão(ões)",
            len(self._nodes),
            len(data.get("wires", [])),
        )

    def _teardown(self):
        """Desinscreve os InputNodes ativos antes de recarregar."""
        for node in self._input_nodes:
            self.event_bus.unsubscribe(Events.Device.VALIDATED, node.on_event)

        self._nodes = {}
        self._input_nodes = []

    def _build(self, data: dict):
        for node_cfg in data.get("nodes", []):
            node_type = node_cfg.get("type")
            node_id = node_cfg.get("id")
            config = node_cfg.get("config", {})

            node_class = NODE_REGISTRY.get(node_type)

            if not node_class:
                _LOGGER.warning("Tipo de nó desconhecido: %s (id=%s)", node_type, node_id)
                continue

            self._nodes[node_id] = node_class(node_id, config, self.registry)

        for wire in data.get("wires", []):
            source = self._nodes.get(wire.get("from"))
            target = self._nodes.get(wire.get("to"))

            if not source or not target:
                _LOGGER.warning("Conexão inválida no flow: %s", wire)
                continue

            source.add_output(target)

        for node in self._nodes.values():
            if isinstance(node, InputNode):
                self.event_bus.subscribe(Events.Device.VALIDATED, node.on_event)
                self._input_nodes.append(node)

    async def save_and_reload(self, data: dict):
        """Salva o novo flow no disco e recarrega o runner."""
        self.flows_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        await self.reload()

    def get_flow(self) -> dict:
        """Retorna o conteúdo atual de automations.json."""
        if not self.flows_path.exists():
            return {"nodes": [], "wires": []}

        return json.loads(self.flows_path.read_text(encoding="utf-8"))
