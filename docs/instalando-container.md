# Instalando e Desenvolvendo a Dispatcher em modo Docker Container

## Instalação do Projeto

Clone o repositório da Dispatcher no seu Raspberry.

```bash
git clone https://github.com/the-bifrost/dispatcher.git
```

Entre no diretório raiz do projeto

```bash
cd dispatcher
```

Tendo o projeto clonado, garanta que:

- O ambiente virtual do python está instalado e ativo.
- Você tem o docker instalado no sistema.
- As configurações do projeto, em `config/` estão corretas.

Garanta que existe um arquivo docker-compose.yaml na raiz do seu projeto

```yaml
services:
  bifrost:
    build: .
    volumes:
      - /dev:/dev
      - ./dispatcher:/app/dispatcher
      - ./config:/app/config
      - ./logs:/app/logs
    restart: unless-stopped
```

Após isso, faça o build do container:

```bash
docker compose build
```

E rode o projeto com

```bash
docker compose up -d
```

---

## Desenvolvendo com o Container

Sempre que realizar alguma modificação no código ou nas configurações do projeto, só é necessário restartar o container:

```bash
docker compose restart
```

Porém, caso for feita alguma alteração de bibliotecas do python, ou de packages linux, é necessário rebuildar o projeto.

```bash
docker compose build
```