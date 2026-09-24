<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { loadPhases,type Phase } from '../lib/data'
import { useAuth } from '../stores/auth'
import { useI18n } from '../composables/useI18n'
import DashShell from '../components/layout/DashShell.vue'
import CsvResultUpload from '../components/competition/CsvResultUpload.vue'
import ProjectWorkflow from '../components/competition/ProjectWorkflow.vue'
const {t,pick}=useI18n(),{team,refreshMe}=useAuth()
const phase=ref<Phase|null>(null),loading=ref(true),failed=ref(false)
// The current phase and its database settings decide the available workflow.
const interactive=computed(()=>phase.value?.observer_settings?.projects_enabled||phase.value?.observer_settings?.local_sessions_enabled)
onMounted(async()=>{try{await refreshMe();phase.value=(await loadPhases())[0]??null}catch{failed.value=true}finally{loading.value=false}})
</script>
<template>
  <DashShell :kicker="phase?pick(phase.name_en,phase.name_zh):''" :title="pick('Participate','参赛')">
    <p v-if="loading" role="status">{{ t('common.loading') }}</p>
    <p v-else-if="failed" role="alert">{{ pick('Could not load the competition. Please refresh.','比赛信息加载失败，请刷新重试。') }}</p>
    <div v-else-if="!team" class="panel"><p>{{ t('submit.errors.need_team') }}</p><p class="mt-5"><router-link class="btn primary sm" to="/team">{{ t('nav.team') }} →</router-link></p></div>
    <p v-else-if="!phase" class="panel">{{ pick('No competition is available yet.','当前还没有开放的比赛。') }}</p>
    <ProjectWorkflow v-else-if="interactive" />
    <CsvResultUpload v-else :phase="phase" />
  </DashShell>
</template>
