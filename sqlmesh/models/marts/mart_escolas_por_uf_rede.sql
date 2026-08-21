MODEL (
  name marts.mart_escolas_por_uf_rede,
  kind FULL,
  description 'Quantidade de escolas por UF, rede (pública/privada) e ano do Censo Escolar.',
  owner 'time-de-dados',
  tags ('marts', 'censo_escolar'),
  cron '@daily',
  grain (sigla_uf, rede, ano_censo)
);

SELECT
  sigla_uf,
  rede,
  ano_censo,
  COUNT(*) AS qtd_escolas
FROM intermediate.int_escolas_classificadas
GROUP BY sigla_uf, rede, ano_censo
