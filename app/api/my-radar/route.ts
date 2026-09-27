import { NextRequest } from "next/server";
import { DEFAULT_MY_RADAR, type MyRadarProfile } from "@/lib/my-radar";
import { fetchReleaseJson } from "@/lib/release-data";

export const dynamic = "force-dynamic";

const OWNER = "eradinho-max";
const REPO = "radar-medico";
const TAG = "radar-data";
const ASSET_NAME = "my-radar.json";

function sanitizeProfile(input: unknown): MyRadarProfile {
  const source = (input && typeof input === "object" ? input : {}) as Partial<MyRadarProfile>;
  const validDomains = Array.isArray(source.domains)
    ? source.domains.filter((x): x is "contest" | "residency" => x === "contest" || x === "residency")
    : DEFAULT_MY_RADAR.domains;

  return {
    ...DEFAULT_MY_RADAR,
    ...source,
    version: 1,
    enabled: Boolean(source.enabled ?? true),
    domains: validDomains,
    states: Array.isArray(source.states) ? source.states.map(String).slice(0, 27) : [],
    specialties: Array.isArray(source.specialties) ? source.specialties.map(String).slice(0, 80) : [],
    contest_min_salary: Math.max(0, Number(source.contest_min_salary) || 0),
    residency_min_stipend: Math.max(0, Number(source.residency_min_stipend) || 0),
    only_open: Boolean(source.only_open ?? true),
    official_only: Boolean(source.official_only ?? false),
    notify_new: Boolean(source.notify_new ?? true),
    notify_updates: Boolean(source.notify_updates ?? true),
    notify_revisions: Boolean(source.notify_revisions ?? true),
    digest: source.digest === "daily" ? "daily" : "immediate",
  };
}

async function github(path: string, init: RequestInit = {}) {
  const token = process.env.RADAR_GITHUB_TOKEN;
  if (!token) throw new Error("RADAR_GITHUB_TOKEN não configurado");

  return fetch(`https://api.github.com${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "User-Agent": "RadarMedico/1.0",
      ...(init.headers || {}),
    },
  });
}

export async function GET() {
  const profile = await fetchReleaseJson<MyRadarProfile>(ASSET_NAME);
  return Response.json(
    {
      configured: Boolean(process.env.RADAR_GITHUB_TOKEN && process.env.RADAR_ADMIN_PIN),
      profile: profile ? sanitizeProfile(profile) : null,
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}

export async function POST(request: NextRequest) {
  const adminPin = process.env.RADAR_ADMIN_PIN;
  const token = process.env.RADAR_GITHUB_TOKEN;

  if (!adminPin || !token) {
    return Response.json(
      { ok: false, error: "Sincronização operacional ainda não configurada." },
      { status: 503 },
    );
  }

  let body: { pin?: string; profile?: unknown };
  try {
    body = await request.json();
  } catch {
    return Response.json({ ok: false, error: "Dados inválidos." }, { status: 400 });
  }

  if (body.pin !== adminPin) {
    return Response.json({ ok: false, error: "PIN incorreto." }, { status: 401 });
  }

  const profile = sanitizeProfile(body.profile);

  const releaseResponse = await github(
    `/repos/${OWNER}/${REPO}/releases/tags/${TAG}`,
  );
  if (!releaseResponse.ok) {
    return Response.json(
      { ok: false, error: "Não foi possível localizar a base operacional." },
      { status: 502 },
    );
  }

  const release = await releaseResponse.json() as {
    id: number;
    upload_url: string;
    assets?: Array<{ id: number; name: string }>;
  };

  const existing = release.assets?.find((asset) => asset.name === ASSET_NAME);
  if (existing) {
    const deleteResponse = await github(
      `/repos/${OWNER}/${REPO}/releases/assets/${existing.id}`,
      { method: "DELETE" },
    );
    if (!deleteResponse.ok && deleteResponse.status !== 404) {
      return Response.json(
        { ok: false, error: "Não foi possível atualizar o perfil anterior." },
        { status: 502 },
      );
    }
  }

  const uploadBase = release.upload_url.split("{")[0];
  const uploadResponse = await fetch(
    `${uploadBase}?name=${encodeURIComponent(ASSET_NAME)}`,
    {
      method: "POST",
      cache: "no-store",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "RadarMedico/1.0",
      },
      body: JSON.stringify(profile, null, 2),
    },
  );

  if (!uploadResponse.ok) {
    return Response.json(
      { ok: false, error: "Não foi possível salvar o perfil diário." },
      { status: 502 },
    );
  }

  return Response.json(
    { ok: true, profile, message: "Meu Radar diário atualizado." },
    { headers: { "Cache-Control": "no-store" } },
  );
}
