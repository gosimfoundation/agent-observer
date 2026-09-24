<script setup lang="ts">
import { useRoute } from 'vue-router'
import { onMounted, ref } from 'vue'
import { supabase } from '../../lib/supabase'
import { useI18n } from '../../composables/useI18n'
const { t, pick } = useI18n()
const projectsEnabled = ref(false)
onMounted(async () => {
  const { data, error } = await supabase.from('observer_phase_settings').select('phase_id')
    .or('projects_enabled.eq.true,local_sessions_enabled.eq.true').limit(1)
  projectsEnabled.value = !error && Boolean(data?.length)
})
const route = useRoute()
const items = [
  { to: '/dashboard', key: 'dash.title', exact: true },
  { to: '/team', key: 'nav.team' },
  { to: '/submit', key: 'nav.submit', exact: true },
  { to: '/submissions', key: 'nav.submissions' },
  { to: '/profile', key: 'nav.profile', exact: true },
]
const isActive = (item: { to: string; exact?: boolean }) => item.exact ? route.path === item.to : route.path.startsWith(item.to)
</script>

<template>
  <nav class="admin-nav">
    <router-link v-for="item in items" :key="item.to" :to="item.to" :class="{ active: isActive(item) }">{{ t(item.key) }}</router-link>
    <router-link v-if="projectsEnabled" to="/projects" :class="{ active: route.path === '/projects' }">{{ pick('Agent projects', '智能体项目') }}</router-link>
  </nav>
</template>
