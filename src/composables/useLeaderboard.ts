import { onMounted, onUnmounted, ref } from 'vue'

const API = String(import.meta.env.VITE_COSMOSBENCH_LEADERBOARD_API || '')
const STATIC_API = `${import.meta.env.BASE_URL}cosmosbench-leaderboard.json`
export const COSMOSBENCH_URL = String(import.meta.env.VITE_COSMOSBENCH_URL || '#')

export interface LeaderboardEntry {
  rank: number; name: string; score: number | null; science: number | null
  completion: number | null; uniformity: number | null; submissions: number
}
const numberOrNull = (value: unknown) => value == null || value === '' || !Number.isFinite(Number(value)) ? null : Number(value)
function normalize(raw: Record<string, unknown>, index: number): LeaderboardEntry {
  return {
    rank: Number(raw.rank ?? index + 1),
    name: String(raw.team_name ?? raw.agent_name ?? raw.username ?? raw.name ?? '—'),
    score: numberOrNull(raw.total_score ?? raw.score),
    science: numberOrNull(raw.science_score ?? raw.science),
    completion: numberOrNull(raw.completion_rate ?? raw.completion),
    uniformity: numberOrNull(raw.uniformity_score ?? raw.uniformity),
    submissions: Number(raw.submission_count ?? raw.submissions ?? 0),
  }
}
export function useLeaderboard(limit = 20) {
  const entries = ref<LeaderboardEntry[]>([]), loading = ref(true), refreshing = ref(false), error = ref('')
  const updatedAt = ref<Date | null>(null)
  let timer: number | undefined
  async function load() {
    refreshing.value = true; error.value = ''
    try {
      let loaded = false
      for (const endpoint of [API, STATIC_API].filter(Boolean)) {
        try {
          const url = new URL(endpoint, window.location.origin); url.searchParams.set('limit', String(limit))
          const response = await fetch(url, { headers: { Accept: 'application/json' } })
          if (!response.ok) throw new Error(String(response.status))
          const body = await response.json(); const rows = Array.isArray(body) ? body : (body.entries ?? body.data ?? [])
          entries.value = rows.slice(0, limit).map(normalize); updatedAt.value = new Date(); loaded = true; break
        } catch { /* Try the same-origin snapshot next. */ }
      }
      if (!loaded) throw new Error('unavailable')
    } catch { error.value = 'unavailable' }
    finally { loading.value = false; refreshing.value = false }
  }
  onMounted(() => { load(); timer = window.setInterval(load, 60_000) })
  onUnmounted(() => { if (timer) window.clearInterval(timer) })
  return { entries, loading, refreshing, error, updatedAt, reload: load, leaderboardUrl: COSMOSBENCH_URL }
}
