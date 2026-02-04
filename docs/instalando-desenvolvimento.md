# Instalando o Projeto para desenvolvimento.

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
- As configurações do projeto, em `config/` estão corretas.

Após isso, faça a instalação do projeto em modo editável.

```bash
pip install -e .
```

Agora você pode rodar a dispatcher usando o comando

```bash
python -m dispatcher
```