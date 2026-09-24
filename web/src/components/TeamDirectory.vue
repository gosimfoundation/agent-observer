<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useI18n } from '../composables/useI18n'
import { useAuth } from '../stores/auth'
import { supabase } from '../lib/supabase'
import { teamAction } from '../stores/teamNotifications'
import { describeError } from '../lib/errors'
const i18n = useI18n()
const { pick, t } = i18n
const { team, isLoggedIn } = useAuth()
type Entry = { id: string; name: string; member_count: number; max_size: number; is_locked: boolean }
const entries = ref<Entry[]>([]), loading = ref(true), busy = ref(''), error = ref('')
const sent = ref(new Set<string>())
onMounted(async () => {
  const result = await supabase.rpc('team_directory')
  if (result.error) error.value = describeError(result.error, i18n)
  else entries.value = result.data ?? []
  if (isLoggedIn.value) {
    const {data} = await supabase.rpc('my_team_invitations')
    for (const item of data ?? []) if (item.direction==='sent' && item.kind==='request' && item.status==='pending') sent.value.add(item.team_id)
  }
  loading.value = false
})
async function request(entry: Entry) {
  if (busy.value || sent.value.has(entry.id)) return
  busy.value = entry.id; error.value = ''
  try { await teamAction('request_team_join', { p_team_id: entry.id }); sent.value.add(entry.id) }
  catch (e) { error.value = describeError(e, i18n, ['team.errors', 'team']) }
  finally { busy.value = '' }
}
</script>

<template>
  <section id="teams" class="panel mt-8" data-testid="team-directory">
    <div class="hd"><h2>{{ pick('Teams', '队伍列表') }}</h2></div>
    <p class="text2 text-sm mb-4">{{ pick('Choose a team to send a request. You join after its captain accepts.', '点击队伍发送加入申请，队长接受后即可加入。') }}</p>
    <p v-if="error" role="alert" class="errors">{{ error }}</p>
    <p v-if="loading" role="status">{{ t('common.loading') }}</p>
    <p v-else-if="!entries.length" class="text3">{{ t('team.no_open_teams') }}</p>
    <ul v-else class="space-y-3">
      <li v-for="entry in entries" :key="entry.id" class="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-3" :data-team-id="entry.id">
        <div>
          <button v-if="isLoggedIn && !team && !entry.is_locked && entry.member_count < entry.max_size && !sent.has(entry.id)" class="text-left font-semibold underline underline-offset-4" :disabled="!!busy" @click="request(entry)">{{ entry.name }}</button>
          <strong v-else>{{ entry.name }}</strong>
          <span class="text3 ml-3 text-sm">{{ entry.member_count }} / {{ entry.max_size }}</span>
        </div>
        <span v-if="team?.id === entry.id" class="text3 text-sm">{{ pick('Your team', '我的队伍') }}</span>
        <span v-else-if="entry.is_locked" class="text3 text-sm">{{ pick('Not recruiting', '暂停招募') }}</span>
        <span v-else-if="entry.member_count >= entry.max_size" class="text3 text-sm">{{ pick('Full', '已满员') }}</span>
        <router-link v-else-if="sent.has(entry.id)" class="copy-btn" to="/notifications">{{ pick('Request sent · view progress', '已申请 · 查看进度') }}</router-link>
        <router-link v-else-if="!isLoggedIn" class="btn sm" :to="{path:'/register',query:{mode:'login',next:'/teammates#teams'}}">{{ pick('Sign in to request', '登录后申请加入') }}</router-link>
        <button v-else-if="!team" class="btn sm" :disabled="!!busy" @click="request(entry)">{{ busy === entry.id ? t('common.working') : pick('Request to join', '申请加入') }}</button>
        <span v-else class="text3 text-sm">{{ pick('Already in a team', '你已有队伍') }}</span>
      </li>
    </ul>
  </section>
</template>
