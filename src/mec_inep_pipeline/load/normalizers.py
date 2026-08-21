"""Transformações mínimas aplicadas a registros antes da carga no Postgres.

Estas funções são pensadas para serem plugadas em resources dlt via
`resource.add_map(...)`. Elas fazem apenas o "mínimo indispensável" para que
os dados fiquem carregáveis e consistentes — seleção de campos, tratamento de
nulos/vazios e desaninhamento (flatten) de estruturas JSON. Transformações de
negócio (agregações, joins, regras analíticas) ficam a cargo do SQLMesh.

Todas as funções são puras (recebem um dict e retornam um novo dict), o que
facilita testá-las isoladamente em tests/unit/.
"""

from __future__ import annotations

from typing import Any

# Marcadores de "vazio" comumente usados pelos microdados do INEP/MEC.
DEFAULT_NULL_TOKENS: frozenset[str] = frozenset({"", "NA", "N/A", "null", "NULL", "-", "--"})


def select_fields(record: dict[str, Any], fields: list[str]) -> dict[str, Any]:
    """Mantém apenas as chaves listadas em `fields` (ignora as demais).

    Chaves ausentes no registro original são simplesmente omitidas no resultado
    (não geram erro) — isso torna a função tolerante a pequenas variações de
    schema entre arquivos de anos/fontes diferentes.
    """
    return {field: record[field] for field in fields if field in record}


def replace_null_tokens(
    record: dict[str, Any],
    *,
    tokens: frozenset[str] = DEFAULT_NULL_TOKENS,
    replacement: Any = None,
) -> dict[str, Any]:
    """Substitui valores 'vazios' (strings como '', 'NA', '-') por `replacement`.

    Só mexe em valores do tipo `str`; outros tipos (int, float, bool, None,
    dict, list) passam intocados.
    """
    result: dict[str, Any] = {}
    for key, value in record.items():
        if isinstance(value, str) and value.strip() in tokens:
            result[key] = replacement
        else:
            result[key] = value
    return result


def strip_whitespace(record: dict[str, Any]) -> dict[str, Any]:
    """Remove espaços em branco nas pontas de todos os valores string do registro."""
    return {
        key: value.strip() if isinstance(value, str) else value for key, value in record.items()
    }


def flatten_json(
    record: dict[str, Any], *, separator: str = "__", prefix: str = ""
) -> dict[str, Any]:
    """Desaninha (flatten) dicts aninhados em colunas com nome composto.

    Exemplo:
        {"endereco": {"cidade": "Bauru", "uf": "SP"}}
        -> {"endereco__cidade": "Bauru", "endereco__uf": "SP"}

    Listas NÃO são desaninhadas aqui — o dlt já lida nativamente com listas de
    dicts, promovendo-as a tabelas filhas relacionadas por chave estrangeira.
    Isso evita duplicar essa lógica e mantém o comportamento previsível do dlt.
    """
    flat: dict[str, Any] = {}
    for key, value in record.items():
        full_key = f"{prefix}{separator}{key}" if prefix else key
        if isinstance(value, dict):
            flat.update(flatten_json(value, separator=separator, prefix=full_key))
        else:
            flat[full_key] = value
    return flat


def normalize_column_names(record: dict[str, Any]) -> dict[str, Any]:
    """Normaliza nomes de colunas para snake_case minúsculo (evita problemas no Postgres).

    Muitos arquivos do INEP vêm com cabeçalhos em MAIÚSCULO (ex.: 'CO_ENTIDADE').
    O dlt já normaliza nomes de coluna por padrão, mas aplicamos aqui também
    para manter o comportamento explícito e testável.
    """
    return {key.strip().lower().replace(" ", "_"): value for key, value in record.items()}


def apply_minimal_transformations(
    record: dict[str, Any],
    *,
    fields: list[str] | None = None,
) -> dict[str, Any]:
    """Pipeline padrão de transformações mínimas, na ordem recomendada.

    Ordem: desaninha JSON -> normaliza nomes de coluna -> remove espaços
    -> trata nulos/vazios -> (opcional) seleciona campos finais.

    O flatten precisa vir ANTES da normalização de nomes: como ele opera
    recursivamente sobre as chaves originais (ex.: "ENDERECO" + "CIDADE"),
    normalizar primeiro deixaria as chaves aninhadas (dentro do dict) com a
    caixa original, gerando uma chave composta inconsistente do tipo
    "endereco__CIDADE" em vez de "endereco__cidade".

    Esta é a função tipicamente registrada via `resource.add_map(...)`.
    """
    record = flatten_json(record)
    record = normalize_column_names(record)
    record = strip_whitespace(record)
    record = replace_null_tokens(record)
    if fields is not None:
        record = select_fields(record, fields)
    return record
