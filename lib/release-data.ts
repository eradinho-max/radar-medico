const REPO = "eradinho-max/radar-medico";
const RELEASE_TAG = "radar-data";

type ReleaseAsset = {
  name: string;
  browser_download_url: string;
  updated_at?: string;
};

type ReleasePayload = {
  updated_at?: string;
  assets?: ReleaseAsset[];
};

export async function fetchReleaseJson<T = unknown>(assetName: string): Promise<T | null> {
  try {
    const releaseResponse = await fetch(
      `https://api.github.com/repos/${REPO}/releases/tags/${RELEASE_TAG}`,
      {
        cache: "no-store",
        headers: {
          Accept: "application/vnd.github+json",
          "User-Agent": "RadarMedico/1.0",
        },
      },
    );

    if (!releaseResponse.ok) return null;

    const release = (await releaseResponse.json()) as ReleasePayload;
    const asset = release.assets?.find((item) => item.name === assetName);
    if (!asset) return null;

    const version = encodeURIComponent(asset.updated_at || release.updated_at || Date.now().toString());
    const separator = asset.browser_download_url.includes("?") ? "&" : "?";
    const assetResponse = await fetch(
      `${asset.browser_download_url}${separator}v=${version}`,
      {
        cache: "no-store",
        headers: { "User-Agent": "RadarMedico/1.0" },
      },
    );

    if (!assetResponse.ok) return null;
    return (await assetResponse.json()) as T;
  } catch {
    return null;
  }
}
