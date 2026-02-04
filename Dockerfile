#  ___ _  __            _   
# | _ |_)/ _|_ _ ___ __| |_ 
# | _ \ |  _| '_/ _ (_-<  _|
# |___/_|_| |_| \___/__/\__|
#

FROM python:3.12-slim

# Evita que o Python gere arquivos .pyc e permite logs em tempo real
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema necessárias para serial e compilação
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copia apenas os arquivos de definição primeiro para cache de camadas
COPY pyproject.toml README.md ./

# Instala o projeto e suas dependências
# O ponto (.) indica o diretório atual onde está o pyproject.toml
RUN pip install --no-cache-dir .

# Copia o código fonte e as configurações iniciais
COPY dispatcher/ ./dispatcher/
COPY config/ ./config/

# Cria o diretório de logs se não existir
RUN mkdir -p logs

# Comando para iniciar o Dispatcher
ENTRYPOINT ["bifrost"]
CMD ["--config", "config/"]