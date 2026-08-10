"Start Dispatcher."

import argparse
import asyncio
import logging
import logging.config
import sys
from pathlib import Path

from .settings import load_config_file, load_configuration
from .start import start

VERMELHO = "\033[31m"
VERDE = "\033[32m"
AZUL = "\033[34m"
RESET = "\033[0m"


logging.basicConfig(
    level=logging.INFO,
    format=f"{VERDE}%(asctime)s{RESET} | {VERMELHO}%(levelname)s{RESET} | {AZUL}%(filename)s:%(lineno)d{RESET} | %(message)s",  # noqa: E501
)
_LOGGER = logging.getLogger(__name__)


def setup_logging(path: Path):
    """Carrega a configuração dos logs do sistema."""
    logger_config = load_config_file(path)
    logging.config.dictConfig(logger_config)


def ensure_config_path(config_dir: Path) -> None:
    """Valida a existência do diretório de configuração."""

    if not config_dir.is_dir():
        _LOGGER.warning("O diretório de configuração '%s' não foi encontrado", config_dir)
        sys.exit(1)


def get_arguments() -> argparse.Namespace:
    """Interpreta os argumentos da cli."""
    parser = argparse.ArgumentParser(description="Dispatcher: Nucleo central de mensagens IoT.")

    parser.add_argument(
        "-c",
        "--config",
        metavar="path_to_config_dir",
        default="config/",
        help="Caminho para o diretório de configuração que contém config.yaml e logs.yaml",
    )

    return parser.parse_args()


def main() -> int:
    """Start Dispatcher."""
    args = get_arguments()

    config_dir = Path(args.config).resolve()
    ensure_config_path(config_dir)

    _LOGGER.info("Usando diretório de configuração: %s", config_dir)
    settings = load_configuration(config_dir / "config.yaml")

    _LOGGER.info("Configurando logger de eventos")
    setup_logging(config_dir / settings.logger_config_path)

    # Inicia a Dispatcher
    try:
        asyncio.run(start(config_dir, settings))

    except KeyboardInterrupt:
        _LOGGER.info("Recebido comando de encerramento (CTRL + C).")

    except Exception:
        _LOGGER.exception("Erro fatal durante a execução")
        return 1

    _LOGGER.info("Dispatcher encerrado com sucesso.")
    return 0


if __name__ == "__main__":
    # Inicia a Dispatcher e passa o código de retorno para o sistema após finalizar.
    sys.exit(main())
