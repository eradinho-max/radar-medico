import { demoOpportunities } from "@/lib/demo-data";
import { fetchReleaseJson } from "@/lib/release-data";

export const dynamic = "force-dynamic";
export const revalidate = 0;

type Payload = {
  updatedAt?: string | null;
  officialCount?: number;
  auxiliaryCount?: number;
  items?: unknown[];
};

export async function GET() {
  const payload = await fetchReleaseJson<Payload>("opportunities.json");
  const items = Array.isArray(payload?.items) ? payload.items : [];

  if (payload && Array.isArray(payload.items)) {
    return Response.json(
      {
        mode: "live",
        updatedAt: payload.updatedAt ?? null,
        officialCount: payload.officialCount ?? 0,
        auxiliaryCount: payload.auxiliaryCount ?? 0,
        count: items.length,
        items,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  }

  return Response.json(
    {
      mode: "demo",
      updatedAt: null,
      officialCount: 0,
      auxiliaryCount: 0,
      count: demoOpportunities.length,
      items: demoOpportunities,
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
