"Start Dispatcher."

import argparse
import asyncio
import logging
import sys

from pathlib import Path

from . import core

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def get_arguments() -> argparse.Namespace:
    """Interpreta os argumentos da cli."""
    parser = argparse.ArgumentParser(
        description="Dispatcher: Nucleo central de mensagens IoT."
    )

    parser.add_argument(
        "-c",
        "--config",
        metavar="path_to_config_dir",
        default="config",
        help="Caminho para o diretório de configuração que contém config.toml e logs.toml"
    )

    return parser.parse_args()


def main() -> int:
    """Start Dispatcher."""

    args = get_arguments()
    config_path = Path(args.config).resolve()

    if not config_path.is_dir():
        logging.error("Erro: O diretório de configuração '%s' não foi encontrado", config_path)
        return 1
    
    logging.info(f"Usando diretório de configuração: {config_path}")

    try:
        asyncio.run(core.start(config_path=config_path))

    except KeyboardInterrupt:
        logging.info("Recebido comando de encerramento (CTRL + C).")

    except Exception as e:
        logging.exception(f"Erro fatal durante a execução: {e}")
        return 1

    logging.info("Dispatcher encerrado com sucesso.")
    return 0

if __name__ == "__main__":
    # Inicia a execução e passa o código de retorno para o sistema
    sys.exit(main())
