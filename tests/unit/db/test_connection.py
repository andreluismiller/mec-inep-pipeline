"""Testes unitários para mec_inep_pipeline.db.connection.

Nenhum destes testes depende de um Postgres real — `psycopg2.connect` é
mockado. Testes que precisam de um Postgres de verdade ficam em
tests/integration/ (marcados com @pytest.mark.integration).
"""

from __future__ import annotations

import pytest
from pytest_mock import MockerFixture

from mec_inep_pipeline.db.connection import check_connection

pytestmark = pytest.mark.unit


class TestCheckConnection:
    def test_returns_true_when_connection_succeeds(self, mocker: MockerFixture) -> None:
        fake_cursor = mocker.MagicMock()
        fake_conn = mocker.MagicMock()
        fake_conn.cursor.return_value.__enter__.return_value = fake_cursor

        mocker.patch(
            "mec_inep_pipeline.db.connection.psycopg2.connect",
            return_value=fake_conn,
        )
        assert check_connection() is True

    def test_returns_false_when_connection_raises(self, mocker: MockerFixture) -> None:
        mocker.patch(
            "mec_inep_pipeline.db.connection.psycopg2.connect",
            side_effect=OSError("connection refused"),
        )
        assert check_connection() is False
