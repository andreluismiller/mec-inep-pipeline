# Imagem enxuta para caber confortavelmente na cota gratuita de Codespaces
# (2-core / 4GB RAM / 32GB storage no tier free de contas pessoais).
FROM python:3.12-slim-bookworm

# Dependências de sistema:
# - build-essential/libpq-dev: fallback caso algum pacote precise compilar contra libpq
# - git: necessário para o dlt (usa git para versionar pipelines) e para o próprio Codespaces
# - curl/unzip: utilitários gerais
# - postgresql-client: psql para debug rápido dentro do Codespace
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        git \
        curl \
        unzip \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Instala uv (gerenciador de pacotes/projeto) via pip, evitando depender
# do instalador oficial (astral.sh), que pode não estar liberado em redes restritas.
RUN pip install --no-cache-dir uv

# Usuário não-root padrão das imagens devcontainer da Microsoft/GitHub Codespaces
ARG USERNAME=vscode
RUN useradd --create-home --shell /bin/bash ${USERNAME} || true

WORKDIR /workspace

# Garante que o uv instale os venvs dentro do projeto (facilita cache e debug)
ENV UV_PROJECT_ENVIRONMENT=/workspace/.venv \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

USER ${USERNAME}
