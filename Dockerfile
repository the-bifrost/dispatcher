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

# Copia arquivos de definição
COPY pyproject.toml README.md ./

# Copia o fonte
COPY dispatcher/ ./dispatcher/

# Instala o projeto e dependências
RUN pip install --no-cache-dir .

# Copia as configurações
COPY config/ ./config/

# Cria o diretório de logs se não existir
RUN mkdir -p logs

# Comando para iniciar o Dispatcher
ENTRYPOINT ["python", "-m", "dispatcher"]
CMD ["--config", "config/"]