<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../../composables/useI18n'
import { supabase } from '../../lib/supabase'
import { describeError } from '../../lib/errors'
import type { Phase } from '../../lib/data'
import { sha256Hex, randomToken } from '../../lib/storage'
import { useAuth } from '../../stores/auth'
import { useFlash } from '../../stores/flash'
const props=defineProps<{phase:Phase}>()
const i18n=useI18n(),{t,tf,pick}=i18n,router=useRouter(),flash=useFlash()
const {team,isAdmin}=useAuth()
const scenarios=computed(()=>props.phase.scenarios.filter(s=>s.is_active))
const scenario=ref(scenarios.value[0]?.slug??''),title=ref(''),notes=ref('')
const selected=computed(()=>scenarios.value.find(s=>s.slug===scenario.value))
const file=ref<File|null>(null),busy=ref(false),dragging=ref(false),error=ref(''),step=ref(''),used=ref(0)
const canSubmit=computed(()=>props.phase.allow_results && (props.phase.status==='open'||isAdmin.value))
onMounted(async()=>{
  if(team.value){const result=await supabase.rpc('team_daily_count',{p_phase_slug:props.phase.slug});used.value=Number(result.data??0)}
})
function choose(files:FileList|null|undefined){file.value=files?.[0]??null;error.value=''}
function drop(event:DragEvent){dragging.value=false;choose(event.dataTransfer?.files)}
async function submit(){
  const f=file.value;error.value=''
  if(!team.value){error.value=t('submit.errors.need_team');return}
  if(!canSubmit.value){error.value=t('submit.no_phase');return}
  if(!f){error.value=t('submit.errors.file_required');return}
  if(!f.name.toLowerCase().endsWith('.csv')){error.value=t('submit.errors.results_csv');return}
  if(!f.size||f.size>20*1024*1024){error.value=tf('submit.errors.too_large',{mb:20});return}
  if(!selected.value){error.value=t('submit.errors.bad_scenario');return}
  busy.value=true
  try{
    step.value=t('submit.hashing');const sha=await sha256Hex(f)
    step.value=t('submit.uploading')
    const path=`${team.value.id}/${Date.now()}-${randomToken(6)}.csv`
    const upload=await supabase.storage.from('submissions').upload(path,f,{upsert:false,contentType:'text/csv'})
    if(upload.error)throw upload.error
    const result=await supabase.rpc('create_submission',{
      p_phase_slug:props.phase.slug,p_kind:'results',p_scenario_slug:scenario.value,
      p_storage_path:path,p_filename:f.name,p_sha256:sha,p_title:title.value.trim(),p_notes:notes.value.trim(),
    })
    if(result.error)throw result.error
    flash.success(t('flash.submission_queued'));await router.push(`/submissions/${result.data}`)
  }catch(e){error.value=describeError(e,i18n,['submit.errors']);flash.error(error.value)}
  finally{busy.value=false;step.value=''}
}
</script>
<template>
  <section data-testid="csv-workflow" class="dash-grid">
    <form class="panel" @submit.prevent="submit">
      <h2 class="mb-5">{{ pick('Upload your result','上传运行结果') }}</h2>
      <p class="text2 mb-5" data-testid="current-submission-phase">{{ pick(phase.name_en,phase.name_zh) }} · {{ tf('submit.quota_left',{n:Math.max(0,phase.daily_limit-used)}) }}</p>
      <p v-if="!canSubmit" class="text2">{{ t('submit.no_phase') }}</p>
      <p v-if="error" class="errors" role="alert">{{ error }}</p>
      <label class="field"><span>{{ t('submit.scenario') }}</span>
        <select v-model="scenario" data-testid="submit-scenario" :disabled="busy">
          <option v-for="s in scenarios" :key="s.id" :value="s.slug">{{ s.slug }} · {{ s.name }}</option>
        </select>
      </label>
      <p v-if="selected" class="help mb-4" data-testid="submit-wallclock">{{ selected.n_nights??'—' }} {{ t('resources.nights') }} · {{ selected.n_tiles??'—' }} {{ t('resources.tiles_n') }}</p>
      <label class="field border border-dashed border-border-subtle p-5" :class="{'bg-white/10':dragging}" @dragover.prevent="dragging=true" @dragleave.prevent="dragging=false" @drop.prevent="drop">
        <span>{{ pick('decisions.csv · up to 20 MB','decisions.csv · 最大 20 MB') }}</span>
        <input type="file" accept=".csv" data-testid="submit-file" :disabled="busy" @change="choose(($event.target as HTMLInputElement).files)">
        <span v-if="file" class="text2">{{ file.name }}</span>
      </label>
      <label class="field"><span>{{ t('submit.title_field') }}</span><input v-model="title" maxlength="120" :disabled="busy"></label>
      <label class="field"><span>{{ t('submit.notes') }}</span><textarea v-model="notes" rows="3" maxlength="4000" :disabled="busy" /></label>
      <button class="btn primary" type="submit" data-testid="submit-send" :disabled="busy||!canSubmit">{{ busy?step:t('submit.button') }}</button>
    </form>
    <aside class="panel">
      <h2>{{ pick('Your next steps','参与流程') }}</h2>
      <ol class="list-decimal pl-5 text2 space-y-3 mt-4"><li>{{ pick('Run the public scenario on your computer.','在本机运行公开场景。') }}</li><li>{{ pick('Upload the generated decisions.csv for that scenario.','选择对应场景，上传生成的 decisions.csv。') }}</li><li>{{ pick('Review the score and replay in your competition history.','在比赛记录中查看成绩和回放。') }}</li></ol>
      <p class="mt-5"><router-link class="btn sm" to="/resources">{{ t('nav.resources') }} →</router-link></p>
      <p class="mt-3"><router-link class="btn sm" to="/submissions">{{ pick('Competition history','比赛记录') }} →</router-link></p>
    </aside>
  </section>
</template>
