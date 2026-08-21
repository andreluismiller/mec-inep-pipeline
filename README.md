# mec-inep-pipeline

Pipeline de engenharia de dados de ponta a ponta (extração, carga e transformação)
para dados de educação básica do **MEC** e **INEP**, com arquitetura modular:

- **Extração + Carga**: [dlt](https://dlthub.com/) lê fontes em CSV, XLSX e API,
  aplica transformações mínimas e carrega em um schema `raw` no **Postgres**.
- **Transformação analítica**: [SQLMesh](https://sqlmesh.com/) transforma os
  dados carregados em modelos organizados em `staging` → `intermediate` → `marts`.
- **Ambiente de desenvolvimento**: GitHub Codespaces (tier gratuito) via
  `.devcontainer/`, com Postgres local subindo automaticamente via docker-compose.
- **Gerenciador de projeto/pacotes**: [uv](https://docs.astral.sh/uv/).

## Arquitetura do repositório

```
.
├── .devcontainer/          # Codespaces: Dockerfile, docker-compose (app + Postgres), devcontainer.json
├── .github/workflows/      # CI (lint, typecheck, testes unitários + integração, testes SQLMesh)
├── config/                 # YAMLs de configuração (nunca segredos)
│   ├── sources.yaml        #   catálogo de fontes (csv/xlsx/api) e seus metadados de extração
│   ├── api_mappings.yaml   #   correspondência "valor real" -> "identificador de API" (ex.: UF -> código IBGE)
│   ├── pipelines.yaml      #   agrupamento de fontes em pipelines dlt, dataset de destino
│   └── logging.yaml        #   configuração de logging (dictConfig)
├── src/mec_inep_pipeline/  # código-fonte da aplicação
│   ├── config/              #   settings.py (.env via pydantic-settings) + loader.py (YAML)
│   ├── extract/
│   │   ├── sources/         #     um módulo por tipo de fonte: csv_source.py, xlsx_source.py, api_source.py
│   │   └── pipelines/       #     run.py: orquestra os dlt.pipeline() a partir de config/pipelines.yaml
│   ├── load/                #   normalizers.py: seleção de campos, nulos/vazios, flatten de JSON
│   ├── db/                  #   connection.py: helpers de Postgres fora do dlt (checagens, DDL pontual)
│   ├── utils/                #   logging.py
│   └── cli/                  #   main.py: CLI via typer (`mec-inep ...`)
├── sqlmesh/                 # projeto SQLMesh (transformação analítica)
│   ├── config.yaml           #   gateway Postgres (credenciais via env_var, nunca hardcoded)
│   └── models/
│       ├── staging/           #     1:1 com as tabelas raw (cast/rename, sem regra de negócio)
│       ├── intermediate/      #     classificações e regras de negócio intermediárias
│       └── marts/             #     modelos finais, prontos para BI/dashboards
├── tests/
│   ├── unit/                 #   testes unitários (sem dependências externas)
│   ├── integration/           #   testes contra Postgres real (pulam automaticamente se indisponível)
│   └── fixtures/              #   arquivos CSV/XLSX pequenos usados nos testes
├── .env.example              # template de variáveis de ambiente/credenciais
└── pyproject.toml            # dependências (uv) + config de pytest/ruff/mypy
```

## Setup rápido

### Opção 1 — GitHub Codespaces (recomendado)

1. No GitHub, clique em **Code → Codespaces → Create codespace on main**.
2. Aguarde o `postCreateCommand` rodar (cria `.env` a partir de `.env.example` e
   sincroniza as dependências com `uv sync`).
3. Edite o `.env` com credenciais reais (URLs/token das APIs do MEC/INEP) —
   o Postgres local já vem configurado automaticamente pelo docker-compose.
4. Rode `make check` para validar que tudo está funcionando.

### Opção 2 — Localmente

Pré-requisitos: Python 3.12+, Docker (para o Postgres) e
[uv](https://docs.astral.sh/uv/getting-started/installation/) instalados.

```bash
git clone <url-do-repositorio>
cd mec-inep-pipeline
cp .env.example .env          # ajuste as credenciais conforme necessário
uv sync                       # instala todas as dependências (inclusive dev)

# sobe um Postgres local (mesmo docker-compose usado no Codespace)
docker compose -f .devcontainer/docker-compose.yml up -d postgres

make check                    # lint + typecheck + testes
```

## Comandos do dia a dia

Veja `make help` para a lista completa. Os mais usados:

```bash
make test              # roda a suíte de testes (pytest)
make lint               # ruff check
make typecheck           # mypy
make check                # lint + typecheck + test (o que o CI roda)

make extract-list          # lista pipelines/fontes configurados (config/*.yaml)
make db-init-schema         # cria o schema "raw" no Postgres
make extract-run-all         # roda todos os pipelines dlt (extração + carga)

make sqlmesh-test              # testes unitários do SQLMesh (não precisa de Postgres)
make sqlmesh-plan-dev            # aplica os modelos SQLMesh em um ambiente "dev" (precisa de Postgres)
```

Ou diretamente via `uv run`:

```bash
uv run mec-inep --help
uv run mec-inep extract run censo_escolar
uv run mec-inep db check
```

## Como adicionar uma nova fonte de dados

1. Descreva a fonte em **`config/sources.yaml`** (tipo, localização, formato,
   chave primária, tabela de destino). Se algum parâmetro precisar traduzir um
   valor legível para o identificador esperado pela API, adicione a
   correspondência em **`config/api_mappings.yaml`**.
2. Associe a fonte a um pipeline (existente ou novo) em **`config/pipelines.yaml`**.
3. Se o tipo de fonte (`csv`/`xlsx`/`api`) já existir, nenhum código novo é
   necessário — o `extract/pipelines/run.py` monta o dlt resource automaticamente
   a partir do YAML. Para um tipo novo, crie `extract/sources/<tipo>_source.py`
   seguindo o padrão dos módulos existentes e registre-o em `_SOURCE_BUILDERS`
   (`extract/pipelines/run.py`).
4. Rode `uv run mec-inep extract run <pipeline>` para carregar os dados.
5. Crie/ajuste os modelos SQLMesh correspondentes em `sqlmesh/models/`.

## Testes

- **Unitários** (`tests/unit/`): rápidos, sem dependências externas — cobrem
  normalizers, loader de config, dispatch de fontes e a CLI.
- **Integração** (`tests/integration/`): exercitam `db/connection.py` contra um
  Postgres real. Pulam automaticamente (não falham) se nenhum Postgres estiver
  acessível — rodam de verdade no Codespace ou no CI.
- **SQLMesh** (`sqlmesh/tests/`): testes unitários de modelos, com dados de
  entrada/saída fixos, usando o motor DuckDB embutido (não precisa de Postgres).

```bash
uv run pytest --cov --cov-report=term-missing   # cobertura da suíte Python
cd sqlmesh && uv run sqlmesh test                # testes dos modelos SQLMesh
```

## Segurança / credenciais

- **Nunca** commite o arquivo `.env` (já está no `.gitignore`). Use `.env.example`
  como template.
- Nenhuma credencial fica hardcoded em `config/*.yaml` ou `sqlmesh/config.yaml` —
  ambos referenciam variáveis de ambiente (`${VAR}` nos YAMLs do dlt/config;
  `{{ env_var('VAR') }}` no `sqlmesh/config.yaml`).
- `src/mec_inep_pipeline/config/settings.py` é a única porta de entrada para
  segredos no código Python — outros módulos nunca devem ler `os.environ`
  diretamente para credenciais.
