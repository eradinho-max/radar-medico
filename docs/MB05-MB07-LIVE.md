# MB05–MB07 — Radar operacional

## MB05 — coleta
- GitHub Actions executa automaticamente.
- Primeiro merge em `main` inicializa a release `radar-data`.
- Depois executa 3×/dia.
- Fontes oficiais iniciais: Ministério da Saúde e HU Brasil/EBSERH.
- PCI é usado somente como descoberta auxiliar em pesquisas médicas específicas.
- Veterinária/biomedicina/odontologia são excluídas.
- Feed operacional contém apenas oportunidades abertas ou futuras detectadas.

## MB06 — alertas
O e-mail é opcional e gratuito por Gmail SMTP. A ausência de credenciais não interrompe coleta.

Segredos esperados:
- `RADAR_EMAIL_TO`
- `GMAIL_SMTP_USER`
- `GMAIL_APP_PASSWORD`

## MB07 — produto live
A API pública lê `opportunities.json` da GitHub Release `radar-data`.
O front-end diferencia:
- fonte oficial;
- descoberta auxiliar;
- fallback demonstrativo.

## Expansão seguinte
A infraestrutura fica congelada. Próximos trabalhos devem ampliar adapters/fontes e enriquecer links oficiais, sem trocar novamente a arquitetura.
