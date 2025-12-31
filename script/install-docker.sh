#!/bin/bash

# Este script baixa e executa o script oficial de instalação do Docker.

# Verifica se o curl está instalado
if ! [ -x "$(command -v curl)" ]; then
  echo 'Erro: curl não está instalado.' >&2
  exit 1
fi

echo "Baixando o script de instalação do Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh

echo "Executando o script de instalação..."
sudo sh get-docker.sh

echo "Limpando o arquivo de instalação..."
rm get-docker.sh

echo "Instalação do Docker concluída."

# Adiciona o usuário atual ao grupo do Docker para executar comandos sem sudo (opcional, mas recomendado)
# É necessário fazer logout e login novamente para que essa alteração tenha efeito.
if [ "$(whoami)" != "root" ]; then
    if groups "$(whoami)" | grep &>/dev/null '\bdocker\b'; then
        echo "O usuário $(whoami) já pertence ao grupo docker."
    else
        echo "Adicionando o usuário $(whoami) ao grupo docker..."
        sudo usermod -aG docker "$(whoami)"
        echo "IMPORTANTE: Faça logout e login novamente para usar o Docker sem 'sudo'."
    fi
fi

echo "Para verificar a instalação, execute: docker --version"