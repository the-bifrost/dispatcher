"Start Dispatcher."

import argparse
import asyncio
import logging
import sys

from pathlib import Path

from dispatcher import core


logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

def ensure_config_path(config_dir: Path) -> None:
    """Valida a existência do diretório de configuração."""

    if not config_dir.is_dir():
        logging.warning("O diretório de configuração '%s' não foi encontrado", config_dir)

        # Se não existir tenta criar o diretório e seus pais, 
        # sem erros, caso já existam.
        try:
            config_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logging.error("Não foi possível criar o diretório de configuração '%s': %s", config_dir, e)
            sys.exit(1)


def get_arguments() -> argparse.Namespace:
    """Interpreta os argumentos da cli."""
    parser = argparse.ArgumentParser(
        description="Dispatcher: Nucleo central de mensagens IoT."
    )

    parser.add_argument(
        "-c",
        "--config",
        metavar="path_to_config_dir",
        default="config/",
        help="Caminho para o diretório de configuração que contém config.toml e logs.toml"
    )

    return parser.parse_args()


def main() -> int:
    """Start Dispatcher."""
    args = get_arguments()
    
    # Monta o caminho absoluto do diretório passado e valida sua existência.
    config_dir = Path(args.config).resolve()
    ensure_config_path(config_dir)

    logging.info("Usando diretório de configuração: %s", config_dir)

    try:
        asyncio.run(core.start(config_path=config_dir))

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
