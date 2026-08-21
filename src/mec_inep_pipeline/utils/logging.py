"""Configuração de logging da aplicação, a partir de config/logging.yaml."""

from __future__ import annotations

import logging
import logging.config

import yaml

from mec_inep_pipeline.config.settings import CONFIG_DIR, REPO_ROOT, get_settings

_configured = False


def setup_logging() -> None:
    """Aplica a configuração de logging (idempotente: só roda uma vez por processo)."""
    global _configured
    if _configured:
        return

    # Garante que o diretório de logs exista (usado pelo RotatingFileHandler)
    (REPO_ROOT / "logs").mkdir(parents=True, exist_ok=True)

    config_path = CONFIG_DIR / "logging.yaml"
    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as f:
            config = yaml.safe_load(f)
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)

    # LOG_LEVEL no .env tem prioridade sobre o "root.level" do YAML
    level = get_settings().log_level.upper()
    logging.getLogger("mec_inep_pipeline").setLevel(level)

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Retorna um logger já configurado, namespaced sob 'mec_inep_pipeline'."""
    setup_logging()
    full_name = name if name.startswith("mec_inep_pipeline") else f"mec_inep_pipeline.{name}"
    return logging.getLogger(full_name)
