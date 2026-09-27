# MB12 — Residências Médicas

Residências Médicas passam a ser um domínio próprio dentro do Radar Médico.

## Princípios

- Mesma infraestrutura FREE-ONLY.
- Aba própria no site.
- Persistência em `residencies.json` na release `radar-data`.
- PassaPro é descoberta auxiliar.
- Fonte oficial encontrada no detalhe recebe prioridade.
- Residência multiprofissional/uniprofissional é excluída.
- Provas de título/exames de especialista não entram como residência.

## Filtros específicos

- UF
- especialidade/programa
- instituição
- tipo de entrada:
  - acesso direto
  - pré-requisito
  - ano adicional
  - área de atuação
- situação:
  - inscrições abertas
  - em breve
- bolsa mínima
- busca textual

## Campos

- instituição
- especialidade
- tipo de entrada
- vagas
- bolsa
- taxa
- data limite
- data da prova
- banca
- fonte oficial
- fonte de descoberta

## Fontes iniciais

1. PassaPro — descoberta estruturada.
2. Links oficiais extraídos das páginas de detalhe.
3. ENARE/HU Brasil/Gov.br como referência oficial nacional.
4. Próxima onda: COREME, universidades e hospitais públicos.
