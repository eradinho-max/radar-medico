import { createHash } from "node:crypto";

export function makeFingerprint(parts: Array<string | null | undefined>) {
  const canonical = parts
    .map(v => (v ?? "").normalize("NFKC").trim().toLowerCase().replace(/\s+/g, " "))
    .join("|");
  return createHash("sha256").update(canonical).digest("hex");
}
