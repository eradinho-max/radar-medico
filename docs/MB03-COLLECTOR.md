# MB03 — Coleta real de editais

## Estado
Primeira camada operacional implementada.

## Fontes iniciais
1. Diário Oficial da União — fonte oficial federal.
2. HU Brasil / EBSERH — concursos e seleções da rede nacional.
3. Ministério da Saúde — concursos e processos seletivos.

## Endpoints
- `GET /api/sources` — catálogo de fontes.
- `GET /api/discover?source=ministerio-saude` — executa descoberta real numa fonte Gov.br.
- `GET /api/discover?source=hu-brasil-concursos` — executa descoberta real na página da rede hospitalar.

## Pipeline
```
fonte
  -> fetch
  -> links candidatos
  -> classificação por termos médicos
  -> fingerprint SHA-256
  -> [próximo] persistência
  -> [próximo] extração do edital
  -> [próximo] versionamento/retificação
```

## Garantias
- URLs oficiais são preservadas.
- Cada candidato recebe fingerprint determinístico.
- O mesmo link não é emitido duas vezes na mesma execução.
- Coleta é server-side.
- Nenhum segredo fica no navegador.
- O adaptador DOU fica separado porque a busca do DOU exige estratégia própria.

## Próxima subcamada
Persistir `sources`, `crawl_runs`, `discovered_documents`, `opportunities` e `opportunity_versions` em Postgres/Supabase.
