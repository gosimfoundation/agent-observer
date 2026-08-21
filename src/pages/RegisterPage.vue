<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { isSupabaseConfigured, supabase } from '../lib/supabase'
import { useI18n } from '../composables/useI18n'
const { pick } = useI18n()
const mode = ref<'register'|'login'|'account'>('register'), loading = ref(false), message = ref(''), userId = ref('')
const form = ref({ name: '', email: '', password: '', github: '', role: '', discord: '', lookingForTeam: true })
const team = ref({ name: '', projectIdea: '', githubRepo: '', maxSize: 4 })
onMounted(async () => { const { data } = await supabase.auth.getSession(); if (data.session) { userId.value = data.session.user.id; mode.value = 'account' } })
async function register() {
  loading.value = true; message.value = ''
  const { data, error } = await supabase.auth.signUp({ email: form.value.email, password: form.value.password, options: { emailRedirectTo: location.origin + import.meta.env.BASE_URL + 'register', data: { name: form.value.name, github_id: form.value.github, role: form.value.role, discord: form.value.discord, looking_for_team: form.value.lookingForTeam } } })
  if (error) message.value = error.message
  else if (data.session) { userId.value = data.user!.id; await saveProfile(); mode.value = 'account'; message.value = pick('Registration complete.', '报名完成。') }
  else message.value = pick('Check your inbox to confirm your email, then return here to log in.', '请查收确认邮件，确认后回到这里登录。')
  loading.value = false
}
async function saveProfile() { if (!userId.value) return; await supabase.from('profiles').upsert({ id: userId.value, name: form.value.name, email: form.value.email, github_id: form.value.github, role: form.value.role, discord: form.value.discord, looking_for_team: form.value.lookingForTeam }) }
async function login() { loading.value = true; message.value = ''; const { data, error } = await supabase.auth.signInWithPassword({ email: form.value.email, password: form.value.password }); if (error) message.value = error.message; else { userId.value = data.user.id; mode.value = 'account'; message.value = pick('Logged in.', '登录成功。') }; loading.value = false }
async function createTeam() { loading.value = true; message.value = ''; const { data, error } = await supabase.from('teams').insert({ name: team.value.name, leader_id: userId.value, project_idea: team.value.projectIdea, github_repo: team.value.githubRepo, max_size: team.value.maxSize }).select('id').single(); if (error) message.value = error.message; else { await supabase.from('profiles').update({ team_id: data.id, looking_for_team: false }).eq('id', userId.value); message.value = pick('Team created.', '队伍创建成功。') }; loading.value = false }
async function logout() { await supabase.auth.signOut(); userId.value = ''; mode.value = 'login' }
</script>
<template>
  <main class="min-h-[75vh] bg-bg-primary py-20"><div class="mx-auto max-w-3xl px-6"><span class="section-kicker">{{ pick('Registration', '报名系统') }}</span><h1 class="section-title mt-6">{{ pick('Join Cosmos26', '加入 Cosmos26') }}</h1><p class="mt-5 text-text-secondary">{{ pick('Registration and teams follow Factory26, but live in a separate Cosmos26 database.', '报名与组队流程沿用 Factory26，但数据存储在独立的 Cosmos26 数据库。') }}</p>
    <div v-if="!isSupabaseConfigured" class="mt-8 border border-accent p-5 text-sm text-text-secondary">{{ pick('Set this site’s own VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY before registration can open.', '请先配置本站独立的 VITE_SUPABASE_URL 和 VITE_SUPABASE_ANON_KEY，之后才能开放报名。') }}</div>
    <div v-else class="mt-10 border-t border-border pt-8"><div v-if="mode !== 'account'" class="mb-7 flex gap-5"><button class="mono-label" :class="mode === 'register' ? 'text-accent' : 'text-text-muted'" @click="mode='register'">{{ pick('Register', '报名') }}</button><button class="mono-label" :class="mode === 'login' ? 'text-accent' : 'text-text-muted'" @click="mode='login'">{{ pick('Login', '登录') }}</button></div>
      <form v-if="mode === 'register'" class="grid gap-5 md:grid-cols-2" @submit.prevent="register"><input v-model="form.name" required class="field" :placeholder="pick('Name *','姓名 *')"><input v-model="form.email" required type="email" class="field" :placeholder="pick('Email *','邮箱 *')"><input v-model="form.password" required minlength="6" type="password" class="field" :placeholder="pick('Password *','密码 *')"><input v-model="form.github" class="field" placeholder="GitHub"><input v-model="form.role" class="field" :placeholder="pick('Role / background','角色 / 背景')"><input v-model="form.discord" class="field" placeholder="Discord"><label class="flex items-center gap-3 text-sm text-text-secondary"><input v-model="form.lookingForTeam" type="checkbox">{{ pick('I am looking for a team','我正在寻找队伍') }}</label><button class="border border-accent p-3 text-accent" :disabled="loading">{{ pick('Submit registration','提交报名') }}</button></form>
      <form v-else-if="mode === 'login'" class="grid max-w-md gap-5" @submit.prevent="login"><input v-model="form.email" required type="email" class="field" placeholder="Email"><input v-model="form.password" required type="password" class="field" :placeholder="pick('Password','密码')"><button class="border border-accent p-3 text-accent" :disabled="loading">{{ pick('Login','登录') }}</button></form>
      <div v-else><div class="flex justify-between"><h2 class="text-2xl text-text-primary">{{ pick('Create a team', '创建队伍') }}</h2><button class="mono-label text-text-muted" @click="logout">{{ pick('Logout','退出') }}</button></div><form class="mt-6 grid gap-5 md:grid-cols-2" @submit.prevent="createTeam"><input v-model="team.name" required class="field" :placeholder="pick('Team name *','队伍名称 *')"><input v-model.number="team.maxSize" type="number" min="1" class="field" :placeholder="pick('Maximum size','人数上限')"><input v-model="team.githubRepo" class="field md:col-span-2" placeholder="GitHub repository"><textarea v-model="team.projectIdea" class="field min-h-28 md:col-span-2" :placeholder="pick('Project idea / observing strategy','项目想法 / 观测策略')"></textarea><button class="border border-accent p-3 text-accent" :disabled="loading">{{ pick('Create team','创建队伍') }}</button></form></div>
      <p v-if="message" class="mt-6 text-sm text-accent">{{ message }}</p></div>
  </div></main>
</template>
<style scoped>.field{width:100%;border:1px solid var(--color-border);background:var(--color-bg-secondary);padding:.8rem;color:var(--color-text-primary);outline:none}.field:focus{border-color:var(--color-accent)}</style>
