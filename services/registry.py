"""Mantém registro de dispositivos em um arquivo JSON"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from models.devices import Device, MqttDevice
from utils.device_factory import create_device

logger = logging.getLogger(__name__)


class DeviceRegistry():
    def __init__(self, path: str):
        """Inicializa dados e cria um validador de registro."""
        self.path = Path(path)
        self.devices: Dict[str, Device] = self._load()  # Cria um atributo devices que armazena o dicionário dos dispositivos

    def _load(self) -> Dict[str, Device]:
        """Carrega e valida o registro a partir do arquivo JSON."""
        
        if not self.path.exists():
            logger.info("Arquivo '%s' não encontrado. Criando novo registro vazio.", self.path)
            return {}
        
        try:
            raw_text = self.path.read_text('utf-8')
            raw_devices_dict = json.loads(raw_text)

            validated_devices: Dict[str, Device] = {}

            for device_id, device_data in raw_devices_dict.items():
                device_object = create_device(device_data)

                if device_object:
                    validated_devices[device_id] = device_object

            logger.info("Registro de dispositivos carregado. %d dispositivos válidos encontrados.", len(validated_devices))
            return validated_devices
        except json.JSONDecodeError as e:
            logger.error("Falha ao decodificar o JSON do registro '%s': %s", self.path, e)
            raise ValueError("Arquivo JSON do registro está mal formatado.") from e
        except Exception as e:
            logger.error("Ocorreu um erro inesperado ao carregar o registro '%s': %s", self.path, e)
            raise
        
    def save(self) -> None:
        """Salva o registro local em um arquivo JSON."""
        registry_to_save = {
            device_id: device.model_dump(mode='json')
            for device_id, device in self.devices.items()
        }

        try:
            with self.path.open('w', encoding='utf-8') as f:
                # Usamos a nova variável que contém apenas dicionários
                json.dump(registry_to_save, f, indent=4, ensure_ascii=False)
            logger.debug("Registro salvo com sucesso em '%s'", self.path)
        except Exception as e:
            logger.error("Falha ao salvar JSON no arquivo '%s' : '%s'", self.path, e)
            raise

    def get_by_id(self, device_id: str) -> Device | None:
        """Retorna o objeto Device de um dispositivo cadastrado pelo seu ID."""
        return self.devices.get(device_id)
    
    def search(self, **kwargs: Any) -> List[Device]:
        """Busca Dispositivos no registro que correspondem a um ou mais critérios."""
        found_devices: List[Device] = []

        # Se nenhum critério for dado, retorna uma lista vazia
        if not kwargs:
            return found_devices
        
        for device_id, device in self.devices.items():
            is_match =  True

            for key, value in kwargs.items():

                # Verificação especial para o ID do dispositivos, que é a chave do dicionário
                if key == 'device_id' and device_id != value:
                    is_match = False
                    break

                # Usa hetattr para verificar de forma segura se o atibuto existe no objeto 
                # e então se correspondem.
                elif hasattr(device, key) and getattr(device, key) == value:
                    continue
                else:
                    is_match = False
                    break

            if is_match:
                found_devices.append(device)
        
        return found_devices   

    def add(self, device_id: str, device_data: Device) -> bool:
        """Adiciona um dispositivo no registro a partir de um objeto Device."""

        if device_id in self.devices:
            logger.info("Device '%s' já existe no registro, não irá registrar.", device_id)
            return False
        else:
            self.devices[device_id] = device_data
            self.save()
            logger.info("Device '%s' foi registrado!", device_id)
            return True
        
    def get_mqtt_topics(self) -> List[str]:
        """Retorna uma lista de tópicos dos dispositivos MQTT registrados."""
        topics = []

        for device in self.devices.values():
            if isinstance(device, MqttDevice):
                topics.append(device.topic)

        return topics