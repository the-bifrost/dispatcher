"""Mantém registro de dispositivos em um arquivo JSON"""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)

##########################################################################################
#                          Implementação antiga da biblioteca                            #
##########################################################################################

class DeviceRegistry():
    def __init__(self, path: str):
        """Carrega e salva localmente o JSON de configuração (caso não existir, inicia um json vazio). 

        Args:
            path: O caminho até o arquivo json usado para registrar.
        """

        self.path = Path(path)
        self._registry: dict = {}

        if self.path.exists():
            try:
                with self.path.open('r', encoding='utf-8') as f:
                    self._registry = json.load(f)
            except json.JSONDecodeError as e:
                logger.error("Falha ao carregar JSON do arquivo '%s': %s", self.path, e)
                raise ValueError("Arquivo JSON inválido.") from e

        else:
            logger.info("Arquivo '%s' não encontrado. Criando novo registro vazio.", self.path)
            self._registry = {}
            self.save()

    def save(self) -> None:
        """Salva o registro local em um arquivo JSON"""

        try:
            with self.path.open('w', encoding='utf-8') as f:
                json.dump(self._registry, f, indent=4, ensure_ascii=False)
            logger.debug("Registro salvo com sucesso em '%s'", self.path)
        except Exception as e:
            logger.error("Falha ao salvar JSON no arquivo '%s' : '%s'", self.path, e)
            raise

    def get_by_id(self, device_id: str) -> dict | None:
        """Retorna dicionário com informações de dispositivos cadastrados
        
        Retorna o resultado da consulta do id na lista de cadastrados. Dispositivos
        não cadastrados retornam Nulo.

        Args:
            device_id: O id do dispositivo que está sendo buscado.

        Returns:
            Se o dispositivo for encontrado no registro, deve retornar um dicionário com
            suas informações:

            {"protocol": "MQTT", "topic": "/example/state"}
            
            Se o dispositivo não for encontrado, o retorno será None.
        """

        return self._registry.get(device_id)
    
    def get_by_address(self, address: str) -> dict | None:
        """Retorna as informações de dispositivos cadastrados a partir do adress
        
        Recebe um adress/topic e busca na lista de cadastrados, se existir,
        retorna um dicionário com as informações do dispositivo.

        Se não existir, retorna None

        """
        for id, info in self._registry.items():
            if info.get("address") == address or info.get("topic") == address:
                return info
        return None

    def add(self, device_id: str, address: str, protocol: str, **kwargs) -> dict:
        """ Adiciona um dispositivo no registro de dispositivos.

        Recebe os dados para cadastrar um novo dispositivo. Verifica no registro se 
        o device_id está disponível, tenta cadastrar.

        Deve sempre retornar um dicionário com os status do request.

        Args:
            device_id: id desejado para cadastrar o dispositivo
            address/topic: endereço usado pra chegar ao dispositivo.
            protocol: (MQTT, ESPNOW, LORA)

        """

        if device_id in self._registry:
            logger.info("Device '%s' já existe no registro, não irá registrar.", device_id)
            
            response = {
                "status": "already_registered",
                "device_id": device_id
            }

        else:
            self._registry[device_id] = {
                "address": address,
                "protocol": protocol,
                **kwargs
            }

            self.save()
            logger.info("Device '%s' foi registrado!", device_id)

            response = {
                "status": "success",
                "device_id": device_id
            }

        return make_envelope(src = "central", dst = address, msg_type = "register_response", payload = response);