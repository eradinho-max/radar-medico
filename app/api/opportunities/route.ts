import { demoOpportunities } from "@/lib/demo-data";

export async function GET() {
  return Response.json({
    mode: "demo",
    count: demoOpportunities.length,
    items: demoOpportunities
  });
}
