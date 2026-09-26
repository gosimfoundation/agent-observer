/**
 * The home page's official demo: the baseline agent's full 180-night run on the public dev-reference
 * scenario, rendered by the platform's own scorer and replay renderer (scripts/build-demo-replay.py).
 * The page ships gzipped as-is; the browser inflates it, so no host-side encoding is assumed.
 * Paths are relative to the site base; callers resolve them with assetUrl.
 */
export const DEMO_REPLAY = { page: '/demo/baseline-dev-reference.html.gz', facts: '/demo/baseline-dev-reference.json' }

export interface DemoReplayFacts {
  scenario: string; scenario_id: string; seed: number; agent: string; score: number
  rounds: number; nights: number; termination: string; decisions_sha256: string; replay_sha256: string
}

const isGzip = (b: Uint8Array) => b.length > 2 && b[0] === 0x1f && b[1] === 0x8b

/** Text of a gzipped file. A host that already decoded it (Content-Encoding: gzip) hands over plain bytes, which pass through. */
export async function inflateText(bytes: Uint8Array): Promise<string> {
  if (!isGzip(bytes)) return new TextDecoder().decode(bytes)
  if (typeof DecompressionStream === 'function') {
    const stream = new Blob([bytes as BlobPart]).stream().pipeThrough(new DecompressionStream('gzip'))
    return new Response(stream).text()
  }
  const { gunzipSync } = await import('fflate')
  return new TextDecoder().decode(gunzipSync(bytes))
}

export async function loadDemoReplayPage(url: string): Promise<string> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`demo replay: ${res.status}`)
  return inflateText(new Uint8Array(await res.arrayBuffer()))
}

export async function loadDemoReplayFacts(url: string): Promise<DemoReplayFacts> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(`demo facts: ${res.status}`)
  return res.json()
}
