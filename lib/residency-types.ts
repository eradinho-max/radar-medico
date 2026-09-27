export type ResidencyStatus = "open" | "upcoming" | "closed" | "reference";

export type ResidencyOpportunity = {
  id: string;
  title: string;
  institution: string;
  city: string;
  state: string;
  specialty: string;
  entryType: string;
  stipend: number | null;
  vacancies: string | null;
  deadline: string | null;
  status: ResidencyStatus;
  examDate: string | null;
  fee: number | null;
  board: string | null;
  officialUrl: string | null;
  sourceUrl: string | null;
  sourceName: string;
  sourceType: "official" | "aggregator" | "demo";
  updatedAt: string;
  fingerprint: string;
};
