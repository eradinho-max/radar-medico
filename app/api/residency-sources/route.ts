const DATA_URL =
  "https://github.com/eradinho-max/radar-medico/releases/download/radar-data/residency-source-health.json";

export const revalidate = 300;

export async function GET() {
  try {
    const response = await fetch(DATA_URL, {
      next: { revalidate: 300 },
      headers: { "User-Agent": "RadarMedico/0.7" },
    });

    if (response.ok) {
      const payload = await response.json();
      const sources = Array.isArray(payload.sources) ? payload.sources : [];
      const byRegion = sources.reduce(
        (acc: Record<string, number>, source: { region?: string }) => {
          const region = source.region || "Outros";
          acc[region] = (acc[region] || 0) + 1;
          return acc;
        },
        {},
      );
      return Response.json({
        mode: "live",
        updatedAt: payload.updatedAt ?? null,
        total: sources.length,
        healthy: sources.filter((s: { status?: string }) => s.status === "ok").length,
        errors: sources.filter((s: { status?: string }) => s.status === "error").length,
        byRegion,
        sources,
      });
    }
  } catch {}

  return Response.json({
    mode: "initializing",
    updatedAt: null,
    total: 0,
    healthy: 0,
    errors: 0,
    byRegion: {},
    sources: [],
  });
}
