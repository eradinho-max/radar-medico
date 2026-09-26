# Radar Médico

Radar nacional de concursos, processos seletivos e editais para médicos.

## Estado atual
V0.2 — MB01 + MB02.

A interface funciona com dados demonstrativos servidos por uma API interna. Isso evita acoplar a UI ao futuro coletor.

## Rodar localmente
```bash
npm install
npm run dev
```

## Build
```bash
npm run build
npm start
```

## Endpoints
- `/api/health`
- `/api/opportunities`

## Próximo macrobloco
Conectar persistência e coleta real com fontes oficiais, deduplicação e alertas por e-mail.
