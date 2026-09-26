import { classifyMedicalOpportunity } from "@/lib/classifier";
import { makeFingerprint } from "@/lib/fingerprint";

export type DiscoveredCandidate = {
  title: string;
  url: string;
  sourceId: string;
  medical: boolean;
  medicalHits: string[];
  fingerprint: string;
};

function absolutize(href: string, baseUrl: string) {
  try { return new URL(href, baseUrl).toString(); } catch { return null; }
}

function cleanHtml(value: string) {
  return value
    .replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, " ")
    .trim();
}

export async function discoverGovBr(sourceId: string, url: string): Promise<DiscoveredCandidate[]> {
  const response = await fetch(url, {
    headers: { "User-Agent": "RadarMedico/0.3 (+https://radar-medico.vercel.app)" },
    cache: "no-store"
  });
  if (!response.ok) throw new Error(`Fonte respondeu ${response.status}`);
  const html = await response.text();

  const links = Array.from(html.matchAll(/<a\b[^>]*href=["']([^"'#]+)["'][^>]*>([\s\S]*?)<\/a>/gi));
  const seen = new Set<string>();
  const candidates: DiscoveredCandidate[] = [];

  for (const match of links) {
    const href = absolutize(match[1], url);
    const title = cleanHtml(match[2]);
    if (!href || title.length < 8 || seen.has(href)) continue;
    seen.add(href);

    const classification = classifyMedicalOpportunity(`${title} edital concurso processo seletivo`);
    const looksRelevant = /(edital|concurso|processo seletivo|sele[cç][aã]o|m[eé]dic)/i.test(title + " " + href);
    if (!looksRelevant) continue;

    candidates.push({
      title,
      url: href,
      sourceId,
      medical: classification.isMedical,
      medicalHits: classification.medicalHits,
      fingerprint: makeFingerprint([sourceId, title, href])
    });
  }

  return candidates.slice(0, 200);
}
