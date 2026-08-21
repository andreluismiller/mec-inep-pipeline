"""Testes unitários para mec_inep_pipeline.extract.sources.api_source."""

from __future__ import annotations

from typing import Any

import pytest
import responses

from mec_inep_pipeline.extract.sources.api_source import build_api_resource

pytestmark = pytest.mark.unit

API_URL = "https://api.inep.gov.br/v1/indicadores-educacionais"


def _source_config(**overrides: Any) -> dict[str, Any]:
    config: dict[str, Any] = {
        "location": {
            "base_url_env": "INEP_API_BASE_URL",
            "token_env": "INEP_API_TOKEN",
            "endpoint": "/v1/indicadores-educacionais",
        },
        "request": {
            "method": "GET",
            "params": [
                {"name": "uf", "from_mapping": "uf", "value": "São Paulo"},
                {"name": "ano", "static": 2024},
            ],
        },
        "pagination": {
            "type": "page_number",
            "page_param": "pagina",
            "size_param": "tamanhoPagina",
            "page_size": 2,
        },
        "primary_key": ["CO_ENTIDADE"],
        "write_disposition": "merge",
        "destination": {"table": "indicadores_educacionais"},
    }
    config.update(overrides)
    return config


class TestBuildApiResource:
    @responses.activate
    def test_paginates_until_short_page(self) -> None:
        # Página 1: 2 itens (== page_size) -> deve continuar para a página 2
        responses.add(
            responses.GET,
            API_URL,
            json={
                "data": [
                    {"CO_ENTIDADE": 1, "CO_INDICADOR": "IDEB"},
                    {"CO_ENTIDADE": 2, "CO_INDICADOR": "IDEB"},
                ]
            },
            status=200,
        )
        # Página 2: 1 item (< page_size) -> deve parar por aqui
        responses.add(
            responses.GET,
            API_URL,
            json={"data": [{"CO_ENTIDADE": 3, "CO_INDICADOR": "IDEB"}]},
            status=200,
        )

        resource = build_api_resource("indicadores_educacionais_api", _source_config())
        rows = list(resource())

        assert len(rows) == 3
        assert len(responses.calls) == 2

    @responses.activate
    def test_applies_minimal_transformations_to_items(self) -> None:
        responses.add(
            responses.GET,
            API_URL,
            json={"data": [{"CO_ENTIDADE": 1, "OBSERVACAO": "NA"}]},
            status=200,
        )
        resource = build_api_resource("indicadores_educacionais_api", _source_config())
        rows = list(resource())

        assert rows[0]["co_entidade"] == 1
        assert rows[0]["observacao"] is None

    @responses.activate
    def test_stops_on_empty_page(self) -> None:
        responses.add(responses.GET, API_URL, json={"data": []}, status=200)
        resource = build_api_resource("indicadores_educacionais_api", _source_config())
        assert list(resource()) == []
        assert len(responses.calls) == 1

    @responses.activate
    def test_resolves_uf_mapping_into_query_param(self) -> None:
        responses.add(responses.GET, API_URL, json={"data": []}, status=200)
        resource = build_api_resource("indicadores_educacionais_api", _source_config())
        list(resource())

        called_url = responses.calls[0].request.url
        assert called_url is not None
        # "São Paulo" deve ter sido traduzido para o código IBGE "35"
        assert "uf=35" in called_url

    @responses.activate
    def test_sends_bearer_token_when_present(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("INEP_API_TOKEN", "token-secreto")
        responses.add(responses.GET, API_URL, json={"data": []}, status=200)
        resource = build_api_resource("indicadores_educacionais_api", _source_config())
        list(resource())

        auth_header = responses.calls[0].request.headers.get("Authorization")
        assert auth_header == "Bearer token-secreto"
