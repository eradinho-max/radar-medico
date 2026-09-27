export type MyRadarProfile = {
  version: 1;
  enabled: boolean;
  domains: Array<"contest" | "residency">;
  states: string[];
  specialties: string[];
  contest_min_salary: number;
  residency_min_stipend: number;
  only_open: boolean;
  official_only: boolean;
  notify_new: boolean;
  notify_updates: boolean;
  notify_revisions: boolean;
  digest: "immediate" | "daily";
};

export const DEFAULT_MY_RADAR: MyRadarProfile = {
  version: 1,
  enabled: true,
  domains: ["contest", "residency"],
  states: [],
  specialties: [],
  contest_min_salary: 0,
  residency_min_stipend: 0,
  only_open: true,
  official_only: false,
  notify_new: true,
  notify_updates: true,
  notify_revisions: true,
  digest: "immediate",
};

function specialtyMatch(value: string, wanted: string[]) {
  if (!wanted.length) return true;
  const normalized = (value || "").toLowerCase();
  return wanted.some((item) => normalized.includes(item.toLowerCase()));
}

export function contestMatchesMyRadar(item: {
  state?: string;
  specialty?: string;
  salary?: number | null;
  status?: string;
  officialUrl?: string | null;
  sourceType?: string;
}, profile: MyRadarProfile) {
  if (!profile.enabled || !profile.domains.includes("contest")) return false;
  if (profile.states.length && !profile.states.includes(item.state || "")) return false;
  if (!specialtyMatch(item.specialty || "", profile.specialties)) return false;
  if (profile.contest_min_salary && (!item.salary || item.salary < profile.contest_min_salary)) return false;
  if (profile.only_open && item.status !== "open") return false;
  if (profile.official_only && !item.officialUrl && item.sourceType !== "official") return false;
  return true;
}

export function residencyMatchesMyRadar(item: {
  state?: string;
  specialty?: string;
  stipend?: number | null;
  status?: string;
  officialUrl?: string | null;
  editalPdf?: string | null;
  sourceType?: string;
}, profile: MyRadarProfile) {
  if (!profile.enabled || !profile.domains.includes("residency")) return false;
  if (profile.states.length && !profile.states.includes(item.state || "")) return false;
  if (!specialtyMatch(item.specialty || "", profile.specialties)) return false;
  if (profile.residency_min_stipend && (!item.stipend || item.stipend < profile.residency_min_stipend)) return false;
  if (profile.only_open && item.status !== "open") return false;
  if (profile.official_only && !item.editalPdf && !item.officialUrl && item.sourceType !== "official") return false;
  return true;
}
