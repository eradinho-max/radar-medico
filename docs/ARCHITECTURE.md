# Radar Médico — Arquitetura por Macroblocos

## MB01 — Produto e experiência (concluído)
- Interface mobile-first em Next.js.
- Busca e filtros médicos.
- Cards padronizados.
- Favoritos locais.
- Rascunho de alerta por e-mail.
- PWA manifest preparado.

## MB02 — Contrato de dados (concluído)
- Tipo `Opportunity` único para o produto.
- Campo `sourceType` diferencia fonte oficial, agregador e demo.
- `officialUrl` reservado para evidência primária.
- `fingerprint` reservado para deduplicação.
- API `/api/opportunities` já desacopla a interface da origem dos dados.

## MB03 — Coleta real (próximo)
Pipeline: fonte -> descoberta -> download -> extração -> classificação médica -> normalização -> fingerprint -> persistência -> auditoria.

Regras principais:
1. Fonte oficial tem precedência.
2. Agregador nunca substitui edital oficial.
3. Nenhuma oportunidade real entra sem URL de origem verificável.
4. Retificações geram nova versão do registro, não sobrescrita silenciosa.
5. Coletor deve ser idempotente.

## MB04 — Persistência e alertas (próximo)
Tabelas planejadas: `sources`, `opportunities`, `opportunity_versions`, `alerts`, `alert_matches`, `crawl_runs`.

## MB05 — Expansão nacional
- DOU e órgãos federais.
- EBSERH e universidades/hospitais.
- Diários oficiais estaduais.
- Prefeituras e secretarias por prioridade/cobertura.
- Bancas organizadoras.
- Fontes auxiliares para descoberta.

## MB06 — Operação
- Cron agendado.
- Logs e falhas de coleta.
- Monitor de fontes silenciosas.
- Painel de saúde da cobertura.
- Métricas de duplicidade, precisão e atraso.
