export type OpportunityStatus = "open" | "upcoming" | "closed";

export type Opportunity = {
  id: string;
  title: string;
  organization: string;
  city: string;
  state: string;
  specialty: string;
  salary: number | null;
  workload: string | null;
  vacancies: string | null;
  deadline: string | null;
  status: OpportunityStatus;
  modality: "Concurso" | "Processo seletivo" | "Residência" | "Outro";
  officialUrl: string | null;
  sourceUrl?: string | null;
  sourceName: string;
  sourceType: "official" | "aggregator" | "demo";
  updatedAt: string;
  fingerprint: string;
};
