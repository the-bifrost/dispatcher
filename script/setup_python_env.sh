#!/bin/bash

# Nome do ambiente virtual
VENV_NAME=".venv"

echo "🛠️ Iniciando configuração do ambiente Python..."

# 1. Verifica se o python3-venv está instalado (comum faltar no Ubuntu/Debian)
if ! dpkg -l | grep -q python3-venv; then
    echo "⚠️ O pacote python3-venv não foi detectado. Instalando..."
    sudo apt update && sudo apt install -y python3-venv
fi

# 2. Cria o ambiente virtual se ele não existir
if [ ! -d "$VENV_NAME" ]; then
    echo "📦 Criando ambiente virtual em '$VENV_NAME'..."
    python3 -m venv $VENV_NAME
    echo "✅ Ambiente criado com sucesso!"
else
    echo "ℹ️ O ambiente '$VENV_NAME' já existe."
fi

# 3. Atualiza o pip dentro do ambiente (opcional, mas recomendado)
echo "🆙 Atualizando o pip dentro do ambiente..."
./$VENV_NAME/bin/pip install --upgrade pip

echo "-------------------------------------------------------"
echo "🚀 Tudo pronto! Para ativar o ambiente, use o comando:"
echo "source $VENV_NAME/bin/activate"
echo "-------------------------------------------------------"