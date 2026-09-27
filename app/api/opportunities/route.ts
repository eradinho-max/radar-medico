import { demoOpportunities } from "@/lib/demo-data";

const DATA_URL =
  "https://github.com/eradinho-max/radar-medico/releases/download/radar-data/opportunities.json";

export const revalidate = 300;

export async function GET() {
  try {
    const response = await fetch(DATA_URL, {
      next: { revalidate: 300 },
      headers: { "User-Agent": "RadarMedico/0.5" },
    });

    if (response.ok) {
      const payload = await response.json();
      const items = Array.isArray(payload) ? payload : payload.items;

      if (Array.isArray(items) && items.length > 0) {
        return Response.json({
          mode: "live",
          updatedAt: payload.updatedAt ?? null,
          officialCount:
            payload.officialCount ??
            items.filter((item: { sourceType?: string }) => item.sourceType === "official").length,
          auxiliaryCount:
            payload.auxiliaryCount ??
            items.filter((item: { sourceType?: string }) => item.sourceType === "aggregator").length,
          count: items.length,
          items,
        });
      }
    }
  } catch {
    // Mantém o site utilizável se o asset operacional estiver temporariamente indisponível.
  }

  return Response.json({
    mode: "demo",
    updatedAt: null,
    officialCount: 0,
    auxiliaryCount: 0,
    count: demoOpportunities.length,
    items: demoOpportunities,
  });
}
