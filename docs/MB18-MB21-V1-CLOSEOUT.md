# MB18–MB21 — Fechamento da V1

## MB18 — Concursos configuráveis
Concursos deixam de depender de fontes hard-coded e passam a usar:
- `collector/config/contest_sources.json`
- `collector/src/contest_catalog.py`

O catálogo inicial cobre fontes federais e estaduais/municipais em todas as regiões.

## MB19 — Motor unificado de mudanças
`collector/src/change_engine.py` diferencia:
- novo;
- atualizado;
- possível retificação.

A mesma lógica serve concursos e residências.

## MB20 — Alertas filtráveis
Sem banco e sem serviço pago.

Variáveis opcionais no GitHub:
- `RADAR_ALERT_DOMAINS` — contest,residency
- `RADAR_ALERT_STATES` — AL,PE,SP...
- `RADAR_ALERT_SPECIALTIES` — psiquiatria,geriatria...
- `RADAR_ALERT_MIN_VALUE` — salário/bolsa mínima

Secrets continuam:
- `RADAR_EMAIL_TO`
- `GMAIL_SMTP_USER`
- `GMAIL_APP_PASSWORD`

## MB21 — Observabilidade + PWA
Assets:
- opportunities.json
- residencies.json
- contest-source-health.json
- residency-source-health.json
- changes.json
- state.json

APIs:
- /api/opportunities
- /api/residencies
- /api/contest-sources
- /api/residency-sources

PWA:
- manifest final;
- service worker;
- cache do shell;
- atualização network-first;
- fallback offline da interface.

## Regra de operação
A arquitetura V1 está congelada.

Nova cobertura deve ocorrer preferencialmente alterando apenas:
- contest_sources.json
- residency_sources.json

Isso evita novas alterações de infraestrutura e reduz deploys.

## FREE-ONLY
Nenhuma função da V1 depende de banco pago, API paga ou serviço com cobrança obrigatória.
