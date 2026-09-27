const DATA_URL =
  "https://github.com/eradinho-max/radar-medico/releases/download/radar-data/residencies.json";

export const revalidate = 300;

export async function GET() {
  try {
    const response = await fetch(DATA_URL, {
      next: { revalidate: 300 },
      headers: { "User-Agent": "RadarMedico/0.6" },
    });

    if (response.ok) {
      const payload = await response.json();
      const items = Array.isArray(payload) ? payload : payload.items;
      if (Array.isArray(items)) {
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
  } catch {}

  return Response.json({
    mode: "initializing",
    updatedAt: null,
    officialCount: 0,
    auxiliaryCount: 0,
    count: 0,
    items: [],
  });
}
