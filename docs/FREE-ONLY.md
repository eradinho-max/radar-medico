# Arquitetura FREE-ONLY — Radar Médico

Regra de projeto: **custo operacional obrigatório = R$ 0**.

Nenhum componente pode:
- exigir cartão para funcionar;
- exigir plano pago;
- gerar cobrança automática por excedente;
- depender de API paga;
- bloquear o núcleo do produto atrás de upgrade.

## Componentes aprovados

### GitHub
- Repositório público.
- GitHub Actions com runners padrão em repositório público.
- Armazenamento operacional em GitHub Release Assets.
- Secrets do GitHub para credenciais de e-mail.
- Sem banco externo.

### Vercel
- Apenas plano Hobby gratuito para o front-end atual.
- Nenhum add-on pago.
- Nenhum storage pago.
- Nenhuma função dependente de crédito adicional.

## Persistência sem banco pago

O estado operacional será armazenado como assets de uma release fixa, por exemplo:

- `state.json`
- `opportunities.json`
- `changes.json`

A release operacional será identificada pela tag `radar-data`.

O GitHub Action:
1. baixa o asset atual;
2. executa os coletores;
3. classifica e deduplica;
4. atualiza os JSONs;
5. substitui os assets da release;
6. envia e-mail quando houver correspondência.

Como o asset é atualizado via Release API/CLI, **não há commit de dados no main e não há novo deploy do Vercel a cada coleta**.

## Alertas por e-mail

Fase pessoal:
- envio via conta Gmail/SMTP usando segredo do GitHub;
- sem plataforma de e-mail paga;
- endereço e credencial ficam em GitHub Secrets, nunca no código.

Se o projeto evoluir para múltiplos usuários, a solução deve continuar respeitando a regra de custo zero; qualquer componente que passe a cobrar será substituído.

## Fonte de verdade

A prioridade continua:

1. fonte oficial;
2. banca organizadora;
3. agregador apenas para descoberta.

Uma oportunidade só será publicada como confiável quando tiver `officialUrl`.

## Limites operacionais

O projeto deve permanecer pequeno o suficiente para os limites gratuitos das plataformas. Se algum limite for atingido, a reação correta é reduzir frequência, compactar dados ou trocar de tecnologia — **não ativar cobrança**.
