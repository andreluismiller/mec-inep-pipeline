MODEL (
  name intermediate.int_escolas_classificadas,
  kind VIEW,
  description 'Classifica escolas por rede (pública/privada) a partir da dependência administrativa.',
  owner 'time-de-dados',
  tags ('intermediate', 'censo_escolar')
);

-- Códigos de dependência administrativa vêm de config/api_mappings.yaml
-- (1=Federal, 2=Estadual, 3=Municipal, 4=Privada).
SELECT
  id_escola,
  nome_escola,
  sigla_uf,
  ano_censo,
  cd_dependencia_administrativa,
  CASE cd_dependencia_administrativa
    WHEN '1' THEN 'publica'
    WHEN '2' THEN 'publica'
    WHEN '3' THEN 'publica'
    WHEN '4' THEN 'privada'
    ELSE 'nao_informado'
  END AS rede
FROM staging.stg_censo_escolar_escolas
