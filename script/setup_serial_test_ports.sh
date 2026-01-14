#!/bin/bash

# 1. Verifica se o socat está instalado
if ! command -v socat &> /dev/null; then
    echo "'socat' não encontrado. Iniciando instalação..."
    
    sudo apt update
    sudo apt install -y socat


    if command -v socat &> /dev/null; then
        echo "'socat' instalado com sucesso!"
    else
        echo "Falha ao instalar o socat."
        exit 1
    fi
else
    echo "'socat' já está instalado."
fi

# 2. Executa o comando
echo "--------------------------------------------------------"
echo "Iniciando portas virtuais..."
echo "ℹSaída esperada: duas linhas indicando /dev/pts/X e /dev/pts/Y"
echo "Pressione [Ctrl+C] para encerrar a simulação."
echo "--------------------------------------------------------"

# Roda o socat
# -d -d: Imprime informações de debug (necessário para ver quais portas foram criadas)
# pty,raw,echo=0: Cria pseudo-terminal sem eco (ideal para simular serial)
socat -d -d pty,raw,echo=0 pty,raw,echo=0