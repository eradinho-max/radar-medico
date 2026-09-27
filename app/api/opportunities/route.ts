import { demoOpportunities } from "@/lib/demo-data";

const DATA_URL =
  "https://github.com/eradinho-max/radar-medico/releases/download/radar-data/opportunities.json";

export const revalidate = 300;

export async function GET() {
  try {
    const response = await fetch(DATA_URL, {
      next: { revalidate: 300 },
      headers: { "User-Agent": "RadarMedico/0.4" },
    });

    if (response.ok) {
      const payload = await response.json();
      const items = Array.isArray(payload) ? payload : payload.items;

      if (Array.isArray(items)) {
        return Response.json({
          mode: "live-free-github-release",
          count: items.length,
          items,
        });
      }
    }
  } catch {
    // Fallback controlado enquanto o asset operacional ainda não existe.
  }

  return Response.json({
    mode: "demo-fallback",
    count: demoOpportunities.length,
    items: demoOpportunities,
  });
}
