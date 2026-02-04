#  ___ _  __            _   
# | _ |_)/ _|_ _ ___ __| |_ 
# | _ \ |  _| '_/ _ (_-<  _|
# |___/_|_| |_| \___/__/\__|
#

FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install --no-install-recommends -y \
        build-essential \
        curl \
        ca-certificates && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copia arquivos de definição
COPY pyproject.toml README.md ./

# Copia o fonte
COPY dispatcher/ ./dispatcher/

# Instala o projeto e dependências
RUN pip install --no-cache-dir .

# Copia as configurações
COPY config/ ./config/

# Comando para iniciar o Dispatcher
ENTRYPOINT ["python", "-m", "dispatcher"]
CMD ["--config", "config/"]