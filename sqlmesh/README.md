# SQLMesh — camada de transformação analítica

Este diretório contém o projeto SQLMesh responsável por transformar os dados
"crus" carregados pelo dlt (schema `raw` no Postgres) em modelos analíticos.

## Estrutura

- `models/staging/` — 1:1 com as tabelas raw; apenas cast de tipos e nomes de negócio (sem regra analítica).
- `models/intermediate/` — junções, classificações e regras de negócio intermediárias.
- `models/marts/` — modelos finais, prontos para consumo por BI/dashboards.
- `seeds/` — dados de referência estáticos versionados como CSV (ex.: tabelas de códigos do INEP).
- `macros/` — macros SQL/Python reutilizáveis entre modelos.
- `audits/` — testes de qualidade de dados (ex.: `NOT NULL`, `UNIQUE`) aplicados a modelos.
- `tests/` — testes unitários de modelos (dados de entrada/saída fixos, sem precisar de Postgres).

## Comandos úteis

```bash
# Carrega as variáveis do .env no shell atual (necessário para o SQLMesh
# resolver os `env_var(...)` em sqlmesh/config.yaml)
set -a && source .env && set +a

cd sqlmesh

uv run sqlmesh test                 # roda os testes unitários (rápidos, sem Postgres)
uv run sqlmesh plan dev             # planeja mudanças em um ambiente de desenvolvimento
uv run sqlmesh plan prod            # planeja/promove mudanças para produção
uv run sqlmesh run                  # executa os modelos agendados (cron)
```

> Pré-requisito: as tabelas em `raw.*` precisam existir (rode os pipelines dlt
> primeiro — `uv run mec-inep extract run-all`).
