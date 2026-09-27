import { fetchReleaseJson } from "@/lib/release-data";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Source = { status?: string; region?: string };
type Payload = { updatedAt?: string | null; sources?: Source[] };

export async function GET() {
  const payload = await fetchReleaseJson<Payload>("contest-source-health.json");
  const sources = Array.isArray(payload?.sources) ? payload.sources : [];

  if (payload && Array.isArray(payload.sources)) {
    const byRegion = sources.reduce((acc: Record<string, number>, source) => {
      const region = source.region || "Outros";
      acc[region] = (acc[region] || 0) + 1;
      return acc;
    }, {});

    return Response.json(
      {
        mode: "live",
        updatedAt: payload.updatedAt ?? null,
        total: sources.length,
        healthy: sources.filter((s) => s.status === "ok").length,
        errors: sources.filter((s) => s.status === "error").length,
        byRegion,
        sources,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  }

  return Response.json(
    { mode: "initializing", updatedAt: null, total: 0, healthy: 0, errors: 0, byRegion: {}, sources: [] },
    { headers: { "Cache-Control": "no-store" } },
  );
}
