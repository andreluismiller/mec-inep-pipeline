.PHONY: help install test test-cov lint format typecheck check \
        db-check db-init-schema extract-list extract-run-all \
        sqlmesh-test sqlmesh-plan-dev clean

help: ## Lista os comandos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Sincroniza as dependências do projeto (uv sync)
	uv sync

test: ## Roda a suíte de testes (pytest)
	uv run pytest -v

test-cov: ## Roda os testes com relatório de cobertura
	uv run pytest --cov --cov-report=term-missing

lint: ## Roda o linter (ruff check)
	uv run ruff check .

format: ## Formata o código (ruff format)
	uv run ruff format .

typecheck: ## Roda o checador de tipos (mypy)
	uv run mypy src/

check: lint typecheck test ## Roda lint + typecheck + testes (usado no CI)

db-check: ## Testa a conexão com o Postgres configurado no .env
	uv run mec-inep db check

db-init-schema: ## Cria o schema de destino (raw) no Postgres
	uv run mec-inep db init-schema

extract-list: ## Lista os pipelines e fontes configurados
	uv run mec-inep extract list

extract-run-all: ## Roda todos os pipelines de extração/carga (dlt)
	uv run mec-inep extract run-all

sqlmesh-test: ## Roda os testes unitários do SQLMesh (não precisa de Postgres)
	cd sqlmesh && uv run sqlmesh test

sqlmesh-plan-dev: ## Planeja mudanças do SQLMesh no ambiente "dev" (precisa de Postgres)
	cd sqlmesh && uv run sqlmesh plan dev

clean: ## Remove caches locais (pytest, mypy, ruff)
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +
