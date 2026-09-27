# MB04A — Núcleo confiável do coletor

## Objetivo
Aproveitar o motor Python recebido sem substituir o front-end Next.js/Vercel.

## Decisões
- O painel HTML/GitHub Pages do ZIP não foi incorporado.
- O disparo de e-mail do ZIP não foi ativado.
- O banco JSON não será usado como fonte de verdade em produção.
- O núcleo de classificação/deduplicação foi reescrito e testado.
- PCI/CNB podem ser usados futuramente apenas como fontes de descoberta.
- Fonte oficial continua sendo requisito para publicação confiável.

## Testes de regressão
- FAMESP/técnico não é vaga médica.
- Médico Psiquiatra é vaga médica.
- Nome de órgão contendo “Médico” não classifica sozinho.
- Item inalterado preserva timestamps.
- URL nova semelhante pode ser marcada como possível retificação.

## Gate para ativar automação
1. Persistência em Postgres/Supabase.
2. Tabela de fontes e execuções.
3. Versionamento de oportunidades.
4. Registro de URL oficial.
5. Só depois: cron + e-mail.
