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
  const payload = await fetchReleaseJson<Payload>("residencies.json");
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
    { mode: "initializing", updatedAt: null, officialCount: 0, auxiliaryCount: 0, count: 0, items: [] },
    { headers: { "Cache-Control": "no-store" } },
  );
}
