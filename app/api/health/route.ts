export async function GET() {
  return Response.json({
    ok: true,
    service: "radar-medico",
    version: "0.2.0",
    dataMode: "demo"
  });
}
