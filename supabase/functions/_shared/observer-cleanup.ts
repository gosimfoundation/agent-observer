import type { Rpc } from "./observer-model.ts";

/** Only temporary uploads selected by the database; no repository/history deletion. */
export async function cleanupUploads(rpc: Rpc, remove: (path: string) => Promise<void>) {
  const uploads = await rpc("observer_expired_uploads", { p_limit: 50 });
  let cleaned = 0;
  for (const upload of uploads) {
    if (!/^[0-9a-f-]{36}\/[0-9a-f-]{36}\/(source\.zip|decisions\.csv)$/.test(upload.path)) continue;
    try {
      await remove(upload.path);
      await rpc("observer_upload_cleaned", { p_upload: upload.id });
      cleaned++;
    } catch {
      // Leave its durable record eligible for the next tick. Never print URLs.
    }
  }
  return cleaned;
}
