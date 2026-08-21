"""Testes de integração: exercitam mec_inep_pipeline.db.connection contra um
Postgres real (não mockado).

Rodam automaticamente:
  - No Codespace, contra o serviço "postgres" do docker-compose do devcontainer.
  - No CI (GitHub Actions), contra o serviço postgres do workflow.

Se nenhum Postgres estiver acessível (ex.: rodando localmente fora do
Codespace, sem docker), os testes são pulados — não falham a suíte inteira.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest

from mec_inep_pipeline.db.connection import check_connection, ensure_schema_exists, fetch_all

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def _skip_if_no_postgres_available() -> Iterator[None]:
    if not check_connection():
        pytest.skip(
            "Nenhum Postgres acessível nas credenciais atuais — pulando testes de "
            "integração. Rode dentro do Codespace (docker-compose) ou no CI."
        )
    yield


class TestPostgresIntegration:
    def test_fetch_all_returns_list_of_dicts(self) -> None:
        rows = fetch_all("SELECT 1 AS um, 'teste' AS texto;")
        assert rows == [{"um": 1, "texto": "teste"}]

    def test_ensure_schema_exists_is_idempotent(self) -> None:
        # Não deve levantar erro ao ser chamada duas vezes seguidas.
        ensure_schema_exists("raw_test_schema")
        ensure_schema_exists("raw_test_schema")

        rows = fetch_all(
            "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s;",
            ("raw_test_schema",),
        )
        assert len(rows) == 1
