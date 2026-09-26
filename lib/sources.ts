export type SourceKind = "official" | "board" | "aggregator";

export type RadarSource = {
  id: string;
  name: string;
  kind: SourceKind;
  scope: "federal" | "national-network" | "state" | "municipal";
  url: string;
  enabled: boolean;
  adapter: "govbr-list" | "dou-search" | "generic-html";
  notes: string;
};

export const radarSources: RadarSource[] = [
  {
    id: "dou",
    name: "Diário Oficial da União",
    kind: "official",
    scope: "federal",
    url: "https://www.in.gov.br/inicio",
    enabled: true,
    adapter: "dou-search",
    notes: "Fonte federal primária. Pesquisa pública e gratuita."
  },
  {
    id: "hu-brasil-concursos",
    name: "HU Brasil / EBSERH — Concursos",
    kind: "official",
    scope: "national-network",
    url: "https://www.gov.br/hubrasil/pt-br/acesso-a-informacao/agentes-publicos/concursos-e-selecoes",
    enabled: true,
    adapter: "govbr-list",
    notes: "Rede nacional de hospitais universitários."
  },
  {
    id: "ministerio-saude",
    name: "Ministério da Saúde — Concursos e Seleções",
    kind: "official",
    scope: "federal",
    url: "https://www.gov.br/saude/pt-br/acesso-a-informacao/concursos-e-selecoes",
    enabled: true,
    adapter: "govbr-list",
    notes: "Concursos e diferentes modalidades de processos seletivos."
  }
];
