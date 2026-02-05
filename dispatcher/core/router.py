"""Roteador de Mensagem. Lê as mudanças de estado e direciona as mensagens para seu destino correto."""

import json
import logging

import aiosqlite

from ..core.device_registry import DeviceRegistry
from ..core.event_bus import event_bus
from ..utils.device import Device
from ..utils.envelope import Envelope
from ..utils.events import Events


_LOGGER = logging.getLogger(__name__)


class Router:
    def __init__(self, db_path: Path):
        _LOGGER.info("Iniciando Router de Mensagens.")

        self._db_path = db_path

        # O Router só ouve mensagens que já foram aprovadas pelo Registry
        event_bus.subscribe(Events.Device.VALIDATED, self.route_message)

        _LOGGER.info("Sucesso ao iniciar o Router!")

    async def route_message(self, data: dict):
        """Recebe um dicionário contendo o envelope e os dados do dispositivo."""

        envelope: Envelope | None = data.get("envelope")
        device: Device | None = data.get("device")

        if not envelope or not device:
            _LOGGER.warning("Dados incompletos para roteamento: %s", data)
            return
        
        destinos = await self.get_route_list(envelope.src)
        
        if not destinos:
            _LOGGER.debug("Nenhuma rota ativa encontrada para o dispositivo %s", envelope.src)
            return
    
        for device_destino in destinos:
            await self.route_state_message(envelope, device_destino)
        
    async def get_route_list(self, device_id: str):
        """Consulta o banco de dados e devolve uma lista de dispositivos que devem receber a mensagem."""
        device_list = []

        async with aiosqlite.connect(self._db_path) as db:
            db.row_factory = aiosqlite.Row

            query = """
                SELECT d.id, d.protocol, d.token, d.config, d.created_at
                FROM devices d
                JOIN routes r ON d.id = r.target_id
                WHERE r.source_id = ? AND r.enabled = 1
            """

            async with db.execute(query, (device_id,)) as cursor:
                async for row in cursor:
                    data = dict(row)

                    if isinstance(data["config"], str):
                        data["config"] = json.loads(data["config"])
                    
                    device_list.append(Device(**data))

        return device_list

    async def route_state_message(self, envelope: Envelope, device_destino: Device):
        """
        Dispara o evento de mudança de estado no protocolo correto.

        Os protocolos devem estar ouvindo "protocol.send_to." + protocol_name 
        Ex: protocol.send_to.mqtt, protocol.send_to.lora
        """
        target_protocol = device_destino.protocol
        event_topic = f"{Events.Protocol.SEND_PREFIX}{target_protocol}"

        _LOGGER.info("Roteando mensagem de '%s' para protocolo '%s'", envelope.src, target_protocol)
        await event_bus.publish(event_topic, {"envelope": envelope, "device": device_destino})



