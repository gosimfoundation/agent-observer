import { ref } from 'vue'
import { supabase } from '../lib/supabase'

export const unreadTeamNotifications = ref(0)
export async function refreshTeamNotifications() {
  const { data, error } = await supabase.rpc('team_invitation_unread')
  if (!error) unreadTeamNotifications.value = Number(data ?? 0)
}
export async function teamAction(name: string, args?: Record<string, unknown>) {
  const { data, error } = await supabase.rpc(name, args)
  if (error) throw error
  await refreshTeamNotifications()
  return data
}
