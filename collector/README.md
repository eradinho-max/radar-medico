# Coletor auxiliar — Radar Médico

Este diretório incorpora apenas o núcleo confiável do motor Python auditado.

## O que foi corrigido

1. **Deduplicação temporal**
   - itens conhecidos preservam `primeira_vez` e `ultima_atualizacao`;
   - um item inalterado não some do histórico;
   - o mesmo edital não reaparece como “novo” em execuções posteriores.

2. **Classificação médica**
   - o nome do órgão não conta como evidência suficiente;
   - cargo tem prioridade sobre título;
   - termos não médicos bloqueiam o uso de “médico/medicina” genérico;
   - o falso positivo da FAMESP com cargos técnicos está coberto por teste.

3. **Possível retificação**
   - URL nova + mesmo órgão/UF + alta similaridade de título é tratada como atualização relacionada;
   - limiar de similaridade: 0,78.

## Por que o agendamento ainda não está ativo

O coletor Python não deve gravar um `banco.json` no mesmo repositório do front-end, porque isso:
- gera commits operacionais desnecessários;
- dispara deploys do Vercel;
- mistura estado de produção com código;
- dificulta auditoria/versionamento.

O próximo passo é persistir o estado em Supabase/Postgres e só então ativar GitHub Actions/cron.

## Testes

```bash
python -m unittest discover -s collector/tests -v
```
