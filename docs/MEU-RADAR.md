# Meu Radar — cadastro e operação diária

## O que o usuário cadastra
O usuário não cadastra concursos ou residências manualmente.

Ele cadastra apenas suas preferências:
- Concursos, residências ou ambos.
- UFs desejadas; nenhuma UF = Brasil inteiro.
- Especialidades; nenhuma = todas.
- Salário mínimo para concursos.
- Bolsa mínima para residências.
- Somente inscrições abertas.
- Somente oportunidades com link oficial validado.
- Tipos de mudança que devem gerar aviso: novo, atualização e retificação.
- Modo de aviso: imediato ou resumo diário.

## Duas camadas

### 1. Meu Radar no navegador
Persistido em `localStorage` na chave:
`radar:my-radar`

Esse perfil:
- aplica filtros imediatamente;
- mostra contagem de concursos compatíveis;
- mostra contagem de residências compatíveis;
- pode ativar “mostrar somente compatíveis”;
- não contém e-mail.

### 2. Meu Radar operacional
Persistido em:
`collector/config/my_radar.json`

O workflow lê esse arquivo em toda execução e usa a mesma lógica para filtrar mudanças antes de enviar e-mail.

O e-mail e a senha de aplicativo nunca entram no repositório. Continuam somente em GitHub Secrets.

## Rotina diária

1. Workflow roda automaticamente três vezes ao dia.
2. Coleta concursos e residências.
3. Deduplica.
4. Verifica novos itens, atualizações e retificações.
5. Aplica `my_radar.json`.
6. Se houver correspondência, o módulo de e-mail prepara o alerta.
7. Se Gmail estiver configurado, envia.
8. Se não houver correspondência, não envia nada.

## Modo resumo diário
Se `digest` for `daily`, apenas a execução da janela matinal envia o resumo.
No modo `immediate`, toda execução pode enviar novidades compatíveis.

## Alteração do perfil operacional
Enquanto a V1 não possui backend autenticado de escrita, o perfil diário é alterado atualizando `my_radar.json`.

Isso pode ser feito pelo assistente diretamente no repositório após o usuário informar as novas preferências.

## Segurança
- E-mail: GitHub Secret.
- Gmail App Password: GitHub Secret.
- Preferências não sensíveis: arquivo JSON.
- Nenhuma credencial é enviada ao navegador.

## Sincronização pelo próprio site

A V1 inclui `POST /api/my-radar`.

O painel “Meu Radar” pode atualizar o perfil operacional sem commit e sem novo deploy.
O perfil é salvo como asset `my-radar.json` na release operacional `radar-data`.

### Ativação inicial única no Vercel

São necessárias duas variáveis secretas:

- `RADAR_ADMIN_PIN`: PIN escolhido pelo administrador para autorizar alterações do perfil.
- `RADAR_GITHUB_TOKEN`: token fine-grained com permissão de leitura/escrita de Contents apenas no repositório `radar-medico`.

Depois dessa configuração:
1. usuário abre “Meu Radar”;
2. escolhe preferências;
3. digita o PIN;
4. clica “Ativar / atualizar alertas diários”;
5. a API atualiza `my-radar.json` na release;
6. a próxima execução do workflow baixa o novo perfil automaticamente.

Nenhum deploy é disparado quando o perfil muda.

### Credenciais de e-mail
Continuam separadas:
- `RADAR_EMAIL_TO`
- `GMAIL_SMTP_USER`
- `GMAIL_APP_PASSWORD`

Essas credenciais ficam somente em GitHub Secrets.
