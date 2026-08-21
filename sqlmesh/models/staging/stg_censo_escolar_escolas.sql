MODEL (
  name staging.stg_censo_escolar_escolas,
  kind VIEW,
  description 'Staging: tipagem e renomeação mínima sobre raw.censo_escolar_escolas (carregada pelo dlt).',
  owner 'time-de-dados',
  tags ('staging', 'censo_escolar')
);

-- Nomes de coluna já vêm em snake_case (ver
-- mec_inep_pipeline.load.normalizers.normalize_column_names aplicado na extração).
-- Aqui fazemos apenas cast de tipos e nomes de negócio -- nenhuma regra analítica.
SELECT
  co_entidade::bigint AS id_escola,
  nome::text AS nome_escola,
  uf::text AS sigla_uf,
  dependencia_administrativa::text AS cd_dependencia_administrativa,
  localizacao::text AS cd_localizacao,
  nu_ano_censo::int AS ano_censo,
  _dlt_load_id AS dlt_load_id,
  _dlt_id AS dlt_id
FROM raw.censo_escolar_escolas
