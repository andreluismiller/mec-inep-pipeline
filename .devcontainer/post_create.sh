#!/usr/bin/env bash
set -euo pipefail

cd /workspace

echo "==> Preparando arquivo .env"
if [ ! -f .env ]; then
    cp .env.example .env
    echo "    .env criado a partir de .env.example — ajuste as credenciais antes de rodar pipelines reais."
else
    echo "    .env já existe, mantendo como está."
fi

echo "==> Sincronizando dependências do projeto com uv"
uv sync --frozen || uv sync

echo "==> Instalando o projeto em modo editável (implícito via 'uv sync')"
uv run python -c "import mec_inep_pipeline; print('Pacote mec_inep_pipeline importável OK')"

echo "==> Verificando ferramentas de linha de comando"
uv run dlt --version || true
uv run sqlmesh --version || true

echo "==> Ambiente pronto. Próximos passos sugeridos:"
echo "    1. Edite .env com credenciais reais (Postgres, APIs do MEC/INEP)."
echo "    2. Rode 'make test' para validar a suíte de testes."
echo "    3. Rode 'uv run python -m mec_inep_pipeline.cli.main --help' para ver os comandos disponíveis."
