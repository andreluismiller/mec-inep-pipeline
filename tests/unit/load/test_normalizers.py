"""Testes unitários para mec_inep_pipeline.load.normalizers."""

from __future__ import annotations

import pytest

from mec_inep_pipeline.load.normalizers import (
    apply_minimal_transformations,
    flatten_json,
    normalize_column_names,
    replace_null_tokens,
    select_fields,
    strip_whitespace,
)

pytestmark = pytest.mark.unit


class TestSelectFields:
    def test_keeps_only_requested_fields(self) -> None:
        record = {"a": 1, "b": 2, "c": 3}
        assert select_fields(record, ["a", "c"]) == {"a": 1, "c": 3}

    def test_ignores_missing_fields_silently(self) -> None:
        record = {"a": 1}
        assert select_fields(record, ["a", "nao_existe"]) == {"a": 1}

    def test_empty_field_list_returns_empty_dict(self) -> None:
        assert select_fields({"a": 1}, []) == {}


class TestReplaceNullTokens:
    @pytest.mark.parametrize("token", ["", "NA", "N/A", "null", "NULL", "-", "--"])
    def test_replaces_known_null_tokens(self, token: str) -> None:
        record = {"campo": token}
        assert replace_null_tokens(record) == {"campo": None}

    def test_does_not_touch_non_string_values(self) -> None:
        record = {"idade": 0, "ativo": False, "nome": None}
        assert replace_null_tokens(record) == record

    def test_strips_before_comparing(self) -> None:
        assert replace_null_tokens({"campo": "  NA  "}) == {"campo": None}

    def test_custom_replacement_value(self) -> None:
        assert replace_null_tokens({"campo": "-"}, replacement="DESCONHECIDO") == {
            "campo": "DESCONHECIDO"
        }

    def test_leaves_real_values_untouched(self) -> None:
        record = {"nome": "Escola Municipal X"}
        assert replace_null_tokens(record) == record


class TestStripWhitespace:
    def test_strips_leading_and_trailing_spaces(self) -> None:
        assert strip_whitespace({"nome": "  Escola X  "}) == {"nome": "Escola X"}

    def test_does_not_touch_non_string_values(self) -> None:
        record = {"ano": 2024, "ativo": True}
        assert strip_whitespace(record) == record


class TestFlattenJson:
    def test_flattens_single_level_nesting(self) -> None:
        record = {"endereco": {"cidade": "Bauru", "uf": "SP"}}
        assert flatten_json(record) == {"endereco__cidade": "Bauru", "endereco__uf": "SP"}

    def test_flattens_multiple_levels(self) -> None:
        record = {"a": {"b": {"c": 1}}}
        assert flatten_json(record) == {"a__b__c": 1}

    def test_leaves_flat_records_untouched(self) -> None:
        record = {"a": 1, "b": "x"}
        assert flatten_json(record) == record

    def test_custom_separator(self) -> None:
        record = {"a": {"b": 1}}
        assert flatten_json(record, separator=".") == {"a.b": 1}

    def test_does_not_flatten_lists(self) -> None:
        # Listas de dicts ficam a cargo do próprio dlt (vira tabela filha).
        record = {"turmas": [{"id": 1}, {"id": 2}]}
        assert flatten_json(record) == record


class TestNormalizeColumnNames:
    def test_lowercases_and_strips_column_names(self) -> None:
        record = {"  CO_ENTIDADE  ": 123, "NO_ENTIDADE": "Escola X"}
        assert normalize_column_names(record) == {"co_entidade": 123, "no_entidade": "Escola X"}

    def test_replaces_spaces_with_underscore(self) -> None:
        record = {"NOME DA ESCOLA": "Escola X"}
        assert normalize_column_names(record) == {"nome_da_escola": "Escola X"}


class TestApplyMinimalTransformations:
    def test_full_pipeline_order(self) -> None:
        record = {
            "  CO_ENTIDADE  ": "  123  ",
            "UF": "NA",
            "ENDERECO": {"CIDADE": " Bauru "},
        }
        result = apply_minimal_transformations(record)
        assert result == {
            "co_entidade": "123",
            "uf": None,
            "endereco__cidade": "Bauru",
        }

    def test_field_selection_applied_last(self) -> None:
        record = {"CO_ENTIDADE": "123", "UF": "SP", "MUNICIPIO": "Bauru"}
        result = apply_minimal_transformations(record, fields=["co_entidade", "uf"])
        assert result == {"co_entidade": "123", "uf": "SP"}
