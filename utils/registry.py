"""Mantém registro de dispositivos em um arquivo JSON"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any

from pydantic import TypeAdapter

from models.devices import Device, EspNowDevice, MqttDevice

logger = logging.getLogger(__name__)

class DeviceRegistry():
    def __init__(self, path: str):
        """Inicializa dados e cria um validador de registro."""
        self.path = Path(path)
        self.devices: Dict[str, Device] = {}
        self._validator = TypeAdapter(Dict[str, Device])

        self.devices = self._load()

    def _load(self) -> Dict[str, Device]:
        """Carrega e valida o registro a partir do arquivo JSON."""
        
        if not self.path.exists():
            logger.info("Arquivo '%s' não encontrado. Criando novo registro vazio.", self.path)
            self.save()
            return {}
        
        try:
            raw_content = self.path.read_text('utf-8')
            validated_devices = self._validator.validate_json(raw_content)

            logger.info("Registro de dispositivos carregado e validado com sucesso!")
            return validated_devices
        except (json.JSONDecodeError, Exception) as e:
            logger.error("Falha ao carregar ou validar o registro '%s': %s", self.path, e)
            raise ValueError("Arquivo JSON inválido ou com dados inconsistentes.") from e
        
    def save(self) -> None:
        """Salva o registro local em um arquivo JSON."""
        # <<< MUDANÇA: Precisamos converter os objetos Pydantic de volta para dicionários
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

    # <<< MUDANÇA: O tipo de retorno agora é um objeto Device!
    def get_by_id(self, device_id: str) -> Device | None:
        """Retorna o objeto Device de um dispositivo cadastrado pelo seu ID."""
        return self.devices.get(device_id)
    
    # <<< MUDANÇA: Retorna um objeto Device e a lógica é mais segura com isinstance
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
        

    # <<< MUDANÇA: A assinatura agora pode aceitar um objeto Device, tornando-a mais flexível
    def add(self, device_id: str, device_data: Device) -> dict:
        """Adiciona um dispositivo no registro a partir de um objeto Device."""
        if device_id in self.devices:
            logger.info("Device '%s' já existe no registro, não irá registrar.", device_id)
            response_payload = { "status": "already_registered", "device_id": device_id }
        else:
            self.devices[device_id] = device_data
            self.save()
            logger.info("Device '%s' foi registrado!", device_id)
            response_payload = { "status": "success", "device_id": device_id }
        
        # O endereço de destino para a resposta depende do tipo de dispositivo
        destination_address = ""
        if isinstance(device_data, EspNowDevice):
            destination_address = device_data.address
        elif isinstance(device_data, MqttDevice):
            destination_address = device_data.topic

        return response_payload