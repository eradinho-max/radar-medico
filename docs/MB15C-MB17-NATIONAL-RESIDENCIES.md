# MB15C–MB17 — Motor nacional de Residências Médicas

## Entrega consolidada

### MB15C — Catálogo nacional configurável
Fontes de residência passam a existir em `collector/config/residency_sources.json`.
Adicionar uma instituição nova não exige alterar o motor principal.

Cobertura inicial do catálogo:
- Nacional: ENARE / HU Brasil
- AL: UNCISAL
- PB: Prefeitura de João Pessoa
- BA: HUPES-UFBA
- GO: HC-UFG
- DF: HUB-UnB
- MG: FHEMIG
- RJ: SES-RJ
- SP: SMS São Paulo
- PA: CHU-UFPA
- rede HU Brasil

As fontes específicas previamente implementadas continuam ativas.

### MB16 — Descoberta institucional genérica
O motor:
1. abre a página da instituição;
2. procura links de residência médica;
3. restringe a anos corrente/próximo ou sinais de inscrições/vagas;
4. exclui multiprofissional/uniprofissional quando não houver evidência médica;
5. cria oportunidade oficial com fingerprint;
6. prioriza PDF de edital quando disponível.

### MB17 — Observabilidade
Cada execução gera:
- `residency-source-health.json`
- status por fonte;
- quantidade de matches;
- latência;
- erro, quando existir;
- resumo por região na API/site.

Endpoint:
- `GET /api/residency-sources`

## Regra operacional
A infraestrutura está congelada. Nova cobertura deve entrar preferencialmente alterando apenas o catálogo JSON, reduzindo commits, deploys e consumo de recursos.

## FREE-ONLY
Nenhum componente deste macrobloco exige serviço pago.
