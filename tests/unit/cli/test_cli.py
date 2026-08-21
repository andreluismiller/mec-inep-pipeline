"""Testes de smoke para mec_inep_pipeline.cli.main (usa typer.testing.CliRunner)."""

from __future__ import annotations

import pytest
from pytest_mock import MockerFixture
from typer.testing import CliRunner

from mec_inep_pipeline.cli.main import app

pytestmark = pytest.mark.unit

runner = CliRunner()


class TestCli:
    def test_help_exits_zero(self) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "extract" in result.output
        assert "db" in result.output

    def test_extract_list_shows_configured_sources(self) -> None:
        result = runner.invoke(app, ["extract", "list"])
        assert result.exit_code == 0
        assert "censo_escolar_escolas" in result.output

    def test_db_check_succeeds_when_connection_ok(self, mocker: MockerFixture) -> None:
        mocker.patch("mec_inep_pipeline.cli.main.check_connection", return_value=True)
        result = runner.invoke(app, ["db", "check"])
        assert result.exit_code == 0

    def test_db_check_fails_when_connection_not_ok(self, mocker: MockerFixture) -> None:
        mocker.patch("mec_inep_pipeline.cli.main.check_connection", return_value=False)
        result = runner.invoke(app, ["db", "check"])
        assert result.exit_code == 1
