import { radarSources } from "@/lib/sources";

export async function GET() {
  return Response.json({
    count: radarSources.length,
    enabled: radarSources.filter(source => source.enabled).length,
    items: radarSources
  });
}
