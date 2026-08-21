"""Testes unitários para mec_inep_pipeline.config.settings."""

from __future__ import annotations

import pytest

from mec_inep_pipeline.config.settings import get_settings

pytestmark = pytest.mark.unit


class TestSettings:
    def test_loads_defaults_from_environment(self) -> None:
        settings = get_settings()
        assert settings.app_env == "test"
        assert settings.postgres_db == "mec_inep_test"

    def test_postgres_dsn_includes_credentials(self) -> None:
        settings = get_settings()
        dsn = settings.postgres_dsn()
        assert "test_user" in dsn
        assert "test_password" in dsn
        assert "mec_inep_test" in dsn

    def test_postgres_dsn_can_hide_password(self) -> None:
        settings = get_settings()
        dsn = settings.postgres_dsn(hide_password=True)
        assert "test_password" not in dsn
        assert "***" in dsn

    def test_settings_is_cached(self) -> None:
        # get_settings() usa lru_cache: duas chamadas devem retornar o MESMO objeto.
        assert get_settings() is get_settings()

    def test_overriding_env_var_reflects_after_cache_clear(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("POSTGRES_DB", "outro_banco")
        get_settings.cache_clear()
        settings = get_settings()
        assert settings.postgres_db == "outro_banco"

    def test_secret_fields_are_not_plain_str(self) -> None:
        settings = get_settings()
        # SecretStr não deve vazar o valor em repr()/str() por acidente.
        assert "test_password" not in repr(settings.postgres_password)
