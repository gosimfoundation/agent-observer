<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { supabase } from '../../lib/supabase'
import { competition } from '../../stores/competition'
import { useAuth } from '../../stores/auth'
import { useI18n } from '../../composables/useI18n'
import { fmtUtc, num } from '../../lib/format'
const props=withDefaults(defineProps<{limit?:number}>(),{limit:50})
const {team}=useAuth(), {pick,t}=useI18n()
type Batch={id:string;status:string;score:number|null;created_at:string}
const rows=ref<Batch[]>([]),loading=ref(true),error=ref(false)
let timer:number|undefined
const statuses=computed(()=>pick<Record<string,string>>({queued:'Queued',starting:'Starting',running:'Running',awaiting_csv:'Waiting for CSV',scored:'Scored',failed:'Failed',cancelled:'Cancelled'}, {queued:'排队中',starting:'启动中',running:'运行中',awaiting_csv:'等待 CSV',scored:'已评分',failed:'失败',cancelled:'已取消'}))
async function load(){
  if(!team.value || !competition.phaseId){loading.value=false;return}
  const result=await supabase.from('observer_batches').select('id,status,score,created_at')
    .eq('team_id',team.value.id).eq('phase_id',competition.phaseId).eq('purpose','formal')
    .order('created_at',{ascending:false}).limit(props.limit)
  error.value=Boolean(result.error)
  if(!result.error)rows.value=result.data??[]
  loading.value=false
}
onMounted(()=>{void load();timer=window.setInterval(()=>{if(!document.hidden)void load()},15000)})
onUnmounted(()=>window.clearInterval(timer))
</script>
<template>
  <section class="panel mb-6" data-testid="evaluation-history">
    <div class="hd"><h2>{{ pick('Evaluations','评测记录') }}</h2><button class="btn sm" @click="load">{{ pick('Refresh','刷新') }}</button></div>
    <p v-if="loading">{{ t('common.loading') }}</p>
    <p v-else-if="error" role="alert">{{ pick('Could not load evaluations. Please refresh.','无法加载评测记录，请刷新重试。') }}</p>
    <p v-else-if="!rows.length" class="text2">{{ pick('No evaluations yet.','还没有评测记录。') }}</p>
    <div v-else class="table-wrap"><table class="data-table">
      <thead><tr><th>{{ t('subs.when') }}</th><th>{{ t('common.status') }}</th><th>{{ t('subs.score') }}</th><th>{{ pick('Details','详情') }}</th></tr></thead>
      <tbody><tr v-for="row in rows" :key="row.id" :data-batch-id="row.id">
        <td class="m xs">{{ fmtUtc(row.created_at) }}</td><td>{{ statuses[row.status]??row.status }}</td><td>{{ num(row.score) }}</td>
        <td><router-link class="accent-l" :to="'/compete#batch-'+row.id">{{ pick('View progress and results','查看进度与结果') }}</router-link></td>
      </tr></tbody>
    </table></div>
    <p class="mt-5"><router-link class="btn primary sm" to="/compete">{{ t('dash.new_submission') }} →</router-link></p>
  </section>
</template>
