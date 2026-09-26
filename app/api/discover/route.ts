import { discoverGovBr } from "@/lib/discovery/govbr";
import { radarSources } from "@/lib/sources";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const requested = searchParams.get("source") ?? "ministerio-saude";
  const source = radarSources.find(item => item.id === requested && item.enabled);

  if (!source) {
    return Response.json({ error: "Fonte desconhecida ou desativada." }, { status: 404 });
  }

  if (source.adapter !== "govbr-list") {
    return Response.json({
      source,
      status: "adapter_pending",
      message: "O adaptador específico desta fonte ainda não foi ativado."
    });
  }

  try {
    const items = await discoverGovBr(source.id, source.url);
    return Response.json({
      source: { id: source.id, name: source.name, url: source.url },
      discoveredAt: new Date().toISOString(),
      count: items.length,
      medicalCandidates: items.filter(item => item.medical).length,
      items
    });
  } catch (error) {
    return Response.json({
      source: { id: source.id, name: source.name, url: source.url },
      error: error instanceof Error ? error.message : "Falha na coleta."
    }, { status: 502 });
  }
}
