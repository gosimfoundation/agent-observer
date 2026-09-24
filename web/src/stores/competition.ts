import { reactive, readonly } from 'vue'
import { isSupabaseConfigured, supabase } from '../lib/supabase'
const state = reactive({ mode: 'practice' as 'practice'|'competition', phaseId: null as string|null })
let fetched = 0, pending: Promise<void>|null = null
export const competition = readonly(state)
export async function loadCompetition(force=false) {
  if (pending) { await pending; return state }
  if (!force && Date.now()-fetched<15000) return state
  pending=(async () => {
    if (!isSupabaseConfigured) return
    const {data,error}=await supabase.rpc('current_competition')
    if (!error && data) {
      state.mode=data.mode==='competition'?'competition':'practice'
      state.phaseId=typeof data.phase_id==='string'?data.phase_id:null
      fetched=Date.now()
    }
  })()
  try { await pending } finally { pending=null }
  return state
}
