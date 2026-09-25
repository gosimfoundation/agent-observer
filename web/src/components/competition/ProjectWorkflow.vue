<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from '../../composables/useI18n'
import { useAuth } from '../../stores/auth'
import { portal, uploadProjectFile, type PortalData, type ProjectRevision } from '../../lib/observerPortal'
import { usePersonalModel } from '../../composables/usePersonalModel'
import { competition } from '../../stores/competition'
const { pick, t } = useI18n()
const { team, refreshMe } = useAuth()
const personal=usePersonalModel()
const data = ref<PortalData | null>(null)
const personalBases=computed(()=>data.value?.model_bases.filter(base=>base.startsWith('https://'))??[])
const loading = ref(true), busy = ref(false), error = ref(''), notice = ref('')
const form = ref({ title: '', kind: 'repository', url: '' })
const selectedFile = ref<File | null>(null), review = ref<ProjectRevision | null>(null)
const reviewPanel = ref<HTMLElement | null>(null)
const phaseId = ref(''), confirmed = ref(false), notes = ref(''), codeUrl = ref('')
const diagnostics = ref<{ kind: string; status: string; code: string; log: string }[] | null>(null)
let timer: ReturnType<typeof setInterval> | undefined
const words = computed(() => pick({
  title: 'Agent projects', intro: 'Submit a complete project, test its interface, then confirm the exact version for evaluation.',
  diagnostics: 'Private run logs', diagnosticsHelp: 'Build and program output is visible only to your team and the organizers.', noLogs: 'No task logs yet.',
  localInfo: 'Local run instructions', runner: 'Download local runner', credential: 'Temporary run credential', copy: 'Copy credential',
  localCommand: 'Extract the runner, replace the project path, and run this command. Paste the credential at its hidden prompt.',
  expires: 'Credential expires', localSecret: 'This credential is only for this run. Do not commit it to a repository.',
  closed: 'Project evaluation is not open for the current competition.',
  csv: 'Existing CSV submission', newProject: 'Submit a project', name: 'Project name', repository: 'Public GitHub repository',
  zip: 'Private ZIP upload', privacy: 'Public repositories remain public after forking. ZIP projects and detailed results are private to your team and the organizers.',
  file: 'Complete project ZIP · up to 50 MB', submit: 'Prepare project', projects: 'Your projects', empty: 'No projects yet.',
  refresh: 'Refresh', review: 'Review interface', explain: 'Adapter explanation', original: 'Original source fingerprint',
  manifest: 'Execution settings', changes: 'Added adapter files', unchanged: 'This project supplies its own interface; no adapter files were added.',
  check: 'I reviewed the execution settings and adapter code, and confirm this exact version.', approve: 'Confirm version',
  testPassed: 'Public scenario test passed', testResult: 'Download public test result', projectDownload: 'Download this project version', phase: 'Evaluation phase', evaluate: 'Evaluate confirmed version',
  batches: 'Evaluations', local: 'Start local CSV session', localHelp: 'Run locally with the same step-by-step information. Upload the resulting decisions.csv after the session.',
  download: 'Download private result', uploadCsv: 'Upload matching CSV', average: 'Combined score',
  api: 'Model APIs', apiHelp: 'Model use is optional. Team keys stay on the server. Set the model parameter to the call name below; OPENAI_BASE_URL and OPENAI_API_KEY are provided for each run. Each run and provider has separate limits.', callName: 'Model call name',
  shared: 'Organizer API', own: 'Team API', modelNames: 'Model names, separated by commas', endpoint: 'API endpoint', key: 'API key',
  apiName: 'API name', edit: 'Edit', limit: 'Daily token limit', saveKey: 'Save encrypted key', disable: 'Disable', enabled: 'Enabled', disabled: 'Disabled',
  evidence: 'Design award evidence', evidenceHelp: 'Describe the architecture and reproducible steps. This does not change performance scores.',
  codeUrl: 'Code or documentation URL (optional)', saveEvidence: 'Save evidence', notes: 'Architecture and reproduction notes',
  close: 'Close review', done: 'Saved.', prepared: 'Project queued for preparation.', confirmed: 'Version confirmed.',
  queued: 'Evaluation queued.', failed: 'This request could not be completed. Refresh and try again.', working: 'Working…',
  team: 'Join or create a team first.', phaseUnavailable: 'No evaluation phase is open.',
}, {
  title: '智能体项目', intro: '提交完整项目，测试接口后，确认用于评测的具体版本。',
  diagnostics: '查看运行日志', diagnosticsHelp: '编译和程序输出只供本队与主办方查看。', noLogs: '暂时没有任务日志。',
  localInfo: '本地运行信息', runner: '下载本地运行器', credential: '本次临时凭证', copy: '复制凭证',
  localCommand: '解压运行器后，替换项目路径并运行下面的命令，按提示粘贴凭证；凭证输入不会显示。',
  expires: '凭证到期时间', localSecret: '凭证只用于这次运行，请勿提交到仓库。',
  closed: '当前比赛尚未开放项目评测。', csv: '原有 CSV 提交', newProject: '提交项目',
  name: '项目名称', repository: '公开 GitHub 仓库', zip: '私有 ZIP 上传',
  privacy: '公开仓库 Fork 后仍然公开；ZIP 项目和详细结果只供本队与主办方查看。', file: '完整项目 ZIP · 最大 50 MB',
  submit: '准备项目', projects: '我的项目', empty: '还没有项目。', refresh: '刷新', review: '检查接口', explain: '适配说明',
  original: '原始代码指纹', manifest: '运行设置', changes: '新增的适配文件', unchanged: '项目自带接口，没有新增适配文件。',
  check: '我已检查运行设置和适配代码，确认使用这个版本。', approve: '确认版本', testPassed: '公开场景测试通过', testResult: '下载公开测试结果', projectDownload: '下载此版本项目',
  phase: '评测赛程', evaluate: '评测已确认版本', batches: '评测记录', local: '启动本地 CSV 会话',
  localHelp: '在本机运行，按步骤获得相同信息；运行结束后上传生成的 decisions.csv。', download: '下载私有结果',
  uploadCsv: '上传匹配的 CSV', average: '综合成绩', api: '模型 API', apiHelp: '模型调用可选，队伍密钥保存在服务器。model 参数使用下方调用名；每次运行会提供 OPENAI_BASE_URL 和 OPENAI_API_KEY。运行与接口均有独立额度。', callName: '模型调用名',
  shared: '主办方接口', own: '队伍接口', modelNames: '模型名称，用逗号分隔', endpoint: 'API 地址', key: 'API 密钥',
  apiName: '接口名称', edit: '修改', limit: '每天最多使用的 token 数', saveKey: '加密保存密钥', disable: '停用', enabled: '已启用', disabled: '已停用',
  evidence: '设计奖材料', evidenceHelp: '说明项目架构和复现步骤；这里不影响实际成绩。', codeUrl: '代码或文档链接（选填）',
  saveEvidence: '保存材料', notes: '架构和复现说明', close: '关闭检查', done: '已保存。', prepared: '项目已排队，等待准备。',
  confirmed: '已确认版本。', queued: '已加入评测队列。', failed: '操作未完成，请刷新后重试。', working: '处理中…',
  team: '请先加入或创建队伍。', phaseUnavailable: '当前没有开放的评测赛程。',
}))
const activePhases = computed(() => (data.value?.phases ?? []).filter(p => (p.phase_id===competition.phaseId||p.phase_id===competition.betaPhaseId) && p.phases.is_active &&
  (!p.phases.ends_at || Date.parse(p.phases.ends_at) > Date.now())))
const projectsOpen = computed(() => activePhases.value.some(p => p.projects_enabled))
const openPhases = computed(() => activePhases.value.filter(p => !p.phases.starts_at || Date.parse(p.phases.starts_at) <= Date.now()))
const selectedPhase = computed(() => openPhases.value.find(p => p.phase_id === phaseId.value))
const statuses = computed(() => pick<Record<string, string>>({ queued:'Queued', preparing:'Preparing', reviewable:'Ready for review', approved:'Confirmed',
  failed:'Failed', starting:'Starting', ready:'Ready', running:'Running', awaiting_csv:'Waiting for CSV', scored:'Scored', cancelled:'Cancelled' },
  { queued:'排队中', preparing:'准备中', reviewable:'等待确认', approved:'已确认', failed:'失败', starting:'启动中', ready:'已就绪',
    running:'运行中', awaiting_csv:'等待 CSV', scored:'已评分', cancelled:'已取消' }))
function errorMessage(e: unknown) {
  const code = e instanceof Error ? e.message : ''
  const messages: Record<string, string> = {
    stale_approval: pick('The version changed. Reopen the review before confirming.', '版本已变化，请重新打开并检查。'),
    csv_does_not_match_session: pick('This CSV differs from the server-recorded decisions.', '这个 CSV 与服务器记录的决策不一致。'),
    batch_already_active: pick('Your team already has an active evaluation.', '本队已有正在进行的评测。'),
    preparation_limit: pick('Your team already has three projects being prepared.', '本队已有三个项目正在准备，请等待完成。'),
    preparation_daily_limit: pick('Your team has used today’s ten project preparations.', '本队今天的十次项目准备机会已用完。'),
    local_session_not_ready: pick('The local engine is not ready yet, or the run has ended. Refresh its status.', '本地会话尚未启动或已经结束，请刷新查看状态。'),
    daily_limit: pick('The daily evaluation limit has been reached.', '今天的评测次数已用完。'),
    wrong_file_type: pick('Choose a file with the required extension.', '请选择要求的文件类型。'),
    file_too_large: pick('The file is empty or exceeds the size limit.', '文件为空或超过大小限制。'),
    invalid_repository_url: pick('Enter a public https://github.com/owner/repository URL.', '请输入公开 GitHub 仓库的完整地址。'),
    model_destination_not_enabled: pick('This API endpoint is not enabled by the organizers.', '这个 API 地址尚未由主办方启用。'),
  }
  return messages[code] ?? words.value.failed
}
async function reload() {
  data.value = await portal<PortalData>('list')
  if(!personal.endpoint.value)personal.endpoint.value=personalBases.value[0]??''
  await personal.refresh()
  // Bind evaluations to the entry phase (beta entry first), never to whatever
  // order the database happened to return.
  const preferred=competition.betaPhaseId??competition.phaseId
  if (!openPhases.value.some(p => p.phase_id === phaseId.value)) phaseId.value = openPhases.value.find(p => p.phase_id===preferred)?.phase_id ?? openPhases.value[0]?.phase_id ?? ''
}
async function action(work: () => Promise<void>, success = words.value.done) {
  if (busy.value) return
  busy.value = true; error.value = ''; notice.value = ''
  try { await work(); await reload(); notice.value = success }
  catch (e) { error.value = errorMessage(e) }
  finally { busy.value = false }
}
function submit() { void action(async () => {
  if (form.value.kind === 'repository') await portal('submit_repository', { title: form.value.title, url: form.value.url })
  else {
    if (!selectedFile.value) throw new Error('wrong_file_type')
    const upload_id = await uploadProjectFile(selectedFile.value, 'source')
    await portal('submit_zip', { title: form.value.title, upload_id })
  }
}, words.value.prepared) }
function openReview(r: ProjectRevision) {
  review.value = r; confirmed.value = false; notes.value = r.observer_evidence?.notes ?? ''; codeUrl.value = r.observer_evidence?.code_url ?? ''
  void nextTick(() => reviewPanel.value?.focus())
}
function approve() { if (review.value && confirmed.value) void action(async () => {
  await portal('approve', { revision_id: review.value!.id, digest: review.value!.approval_digest }); review.value = null
}, words.value.confirmed) }
function evaluate(revision_id: string) { void action(async () => {
  await portal('evaluate', { phase_id: phaseId.value, revision_id })
}, words.value.queued) }
function download(run_id: string) { downloadFile('download_result', { run_id }, 'observer-result.zip') }
function downloadProject(revision_id: string) { downloadFile('download_project', { revision_id }, 'observer-project.zip') }
function downloadFile(command: string, fields: Record<string, unknown>, filename: string) { void action(async () => {
  const result = await portal<{ url: string }>(command, fields)
  const url = new URL(result.url)
  if (url.protocol !== 'https:' && url.hostname !== '127.0.0.1') throw new Error('invalid_download')
  const anchor = document.createElement('a'); anchor.href = url.href; anchor.rel = 'noreferrer'; anchor.download = filename; anchor.click()
}) }
onMounted(async () => {
  await refreshMe()
  try { if (team.value) await reload() } catch (e) { error.value = errorMessage(e) }
  finally { loading.value = false }
  timer = setInterval(() => { if (!busy.value && team.value && !document.hidden) void reload().catch(() => {}) }, 15000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })
</script>

<template>
  <section data-testid="project-workflow">
    <p class="text2 mb-5">{{ words.intro }}</p>
    <p v-if="loading" role="status">{{ t('common.loading') }}</p>
    <p v-else-if="!team" class="panel">{{ words.team }} <router-link to="/team">{{ t('nav.team') }}</router-link></p>
    <template v-else>
      <p v-if="error" class="errors" role="alert" data-testid="project-error">{{ error }}</p>
      <p v-if="notice" role="status" class="mb-4">{{ notice }}</p>
      <p v-if="!projectsOpen" class="panel">{{ words.closed }}</p>
      <details class="panel mb-6" data-testid="personal-model-settings">
        <summary>{{ pick('Use your own model API (optional)','使用自己的模型 API（可选）') }}</summary>
        <p class="help mt-3">{{ pick('No model credits are provided. The key stays only in this page’s memory. Keep this page open during model calls; closing it clears the key.','平台不提供模型额度，密钥只留在当前页面内存中。模型调用期间请保持本页打开，关闭后密钥会清除。') }}</p>
        <form class="mt-4" @submit.prevent="action(personal.connect)">
          <label class="field"><span>{{ pick('API address','API 地址') }}</span><select v-model="personal.endpoint.value" :disabled="personal.connected.value" required><option v-for="base in personalBases" :key="base">{{ base }}</option></select></label>
          <label class="field"><span>{{ pick('Model','模型') }}</span><input v-model="personal.model.value" :disabled="personal.connected.value" maxlength="256" required></label>
          <label class="field"><span>API key</span><input v-model="personal.key.value" type="password" autocomplete="off" :disabled="personal.connected.value" maxlength="8192" required data-testid="personal-api-key"></label>
          <p v-if="!personalBases.length" class="help">{{ pick('No supported HTTPS API address is configured yet. A deterministic project needs no API.','尚未配置受支持的 HTTPS API 地址，确定性算法不需要 API。') }}</p>
          <button v-if="!personal.connected.value" class="btn sm" :disabled="busy||!personalBases.length">{{ pick('Use for this session','仅本次使用') }}</button>
          <button v-else type="button" class="btn sm" @click="personal.clear">{{ pick('Disconnect and clear key','断开并清除密钥') }}</button>
          <p v-if="personal.connected.value" class="help mt-3" role="status">{{ personal.status.value==='failed'?pick('The model call failed. Check your API and quota.','模型调用失败，请检查 API 和额度。'):personal.status.value==='working'?pick('Calling your API…','正在调用你的 API…'):pick('Connected for this page session.','已连接，仅本页会话有效。') }}</p>
        </form>
      </details>
      <p class="mb-5"><button type="button" class="btn sm" :disabled="busy" @click="action(reload)">{{ words.refresh }}</button></p>
      <form v-if="projectsOpen" class="panel mb-6" @submit.prevent="submit">
        <h2 id="prepare">1 · {{ words.newProject }}</h2>
        <label class="field"><span>{{ words.name }}</span><input v-model="form.title" type="text" required maxlength="100" data-testid="project-title"></label>
        <label class="check"><input v-model="form.kind" type="radio" value="repository">{{ words.repository }}</label>
        <label class="check"><input v-model="form.kind" type="radio" value="zip">{{ words.zip }}</label>
        <label v-if="form.kind === 'repository'" class="field"><span>{{ words.repository }}</span><input v-model="form.url" type="url" required placeholder="https://github.com/owner/project" data-testid="project-url"></label>
        <label v-else class="field"><span>{{ words.file }}</span><input type="file" accept=".zip" required data-testid="project-zip" @change="selectedFile = ($event.target as HTMLInputElement).files?.[0] ?? null"></label>
        <p class="help mb-4">{{ words.privacy }}</p>
        <button class="btn primary" :disabled="busy" data-testid="project-submit">{{ busy ? words.working : words.submit }}</button>
      </form>
      <section class="panel mb-6">
        <h2 id="evaluate">2 · {{ pick('Confirm a version and evaluate','确认版本并评测') }}</h2><p v-if="!data?.projects.length" class="text3">{{ words.empty }}</p>
        <p v-if="!openPhases.length" class="help">{{ words.phaseUnavailable }}</p>
        <article v-for="p in data?.projects" :key="p.id" class="project-row">
          <h3>{{ p.title }}</h3>
          <div v-for="r in p.observer_revisions" :key="r.id" class="flex flex-wrap items-center gap-3 mt-3">
            <span class="pill">{{ statuses[r.status] ?? r.status }}</span>
            <span v-if="r.error" class="errors" role="status">{{ r.error }}</span>
            <button class="btn sm" :disabled="busy" @click="action(async () => { diagnostics = await portal('diagnostics', { revision_id: r.id }) })">{{ words.diagnostics }}</button>
            <button v-if="['reviewable','approved'].includes(r.status) || (r.status === 'failed' && r.manifest)" type="button" class="btn sm" @click="openReview(r)">{{ words.review }}</button>
            <button v-if="r.status === 'approved'" type="button" class="btn primary sm" :disabled="busy || !selectedPhase?.projects_enabled" @click="evaluate(r.id)">{{ words.evaluate }}</button>
          </div>
        </article>
      </section>
      <section v-if="review" ref="reviewPanel" tabindex="-1" class="panel mb-6" data-testid="project-review" aria-live="polite">
        <h2>{{ words.review }}</h2><p v-if="review.public_test.passed" class="pill ok mt-3">{{ words.testPassed }}</p>
        <p v-else-if="review.error" class="errors mt-3">{{ review.error }}</p>
        <div class="flex flex-wrap gap-3 mt-3">
          <button class="btn sm" :disabled="busy" @click="downloadProject(review.id)">{{ words.projectDownload }}</button>
          <button v-if="review.public_test.passed && review.public_test.run_id" class="btn sm" :disabled="busy" @click="download(review.public_test.run_id!)">{{ words.testResult }}</button>
        </div>
        <p class="mt-4">{{ words.explain }}: {{ review.explanation }}</p>
        <p class="help break-all">{{ words.original }}: {{ review.source_digest }}</p>
        <h3 class="mt-5">{{ words.manifest }}</h3><pre>{{ JSON.stringify(review.manifest, null, 2) }}</pre>
        <h3 class="mt-5">{{ words.changes }}</h3><p v-if="!Object.keys(review.adapter_files).length" class="help">{{ words.unchanged }}</p>
        <div v-for="(code, path) in review.adapter_files" :key="path"><h4 class="break-all">{{ path }}</h4><pre>{{ code }}</pre></div>
        <template v-if="review.status === 'reviewable'"><label class="check mt-4"><input v-model="confirmed" type="checkbox" data-testid="project-confirm">{{ words.check }}</label>
          <button class="btn primary mt-3" :disabled="busy || !confirmed || !review.public_test.passed" data-testid="project-approve" @click="approve">{{ words.approve }}</button></template>
        <form class="mt-6" @submit.prevent="action(async () => { await portal('evidence', { revision_id: review!.id, notes, code_url: codeUrl }) })">
          <h3>{{ words.evidence }}</h3><p class="help">{{ words.evidenceHelp }}</p>
          <label class="field"><span>{{ words.notes }}</span><textarea v-model="notes" maxlength="8000" rows="5"></textarea></label>
          <label class="field"><span>{{ words.codeUrl }}</span><input v-model="codeUrl" type="url" maxlength="1000"></label>
          <button class="btn sm" :disabled="busy">{{ words.saveEvidence }}</button>
        </form><button class="btn sm mt-4" @click="review = null">{{ words.close }}</button>
      </section>
      <section class="panel mb-6"><h2 id="results">3 · {{ words.batches }}</h2>
        <article v-for="b in data?.batches" :key="b.id" :id="'batch-'+b.id" class="project-row">
          <p>{{ new Date(b.created_at).toLocaleString() }} · {{ statuses[b.status] ?? b.status }}</p>
          <p v-if="b.score != null">{{ words.average }}: {{ b.score.toFixed(2) }}</p>
          <div v-for="run in b.observer_runs" :key="run.id" class="flex flex-wrap gap-3 mt-3 items-center">
            <span class="pill">{{ statuses[run.status] ?? run.status }}</span>
            <span v-if="run.score != null">{{ run.score_summary?.calibration ? t('leaderboard.calibrated_score') + ': ' : '' }}{{ run.score.toFixed(2) }}</span>
            <span v-if="run.score_summary?.raw_score" class="help">{{ t('leaderboard.raw_score') }}: {{ run.score_summary.raw_score.total.toFixed(2) }}</span>
            <button class="btn sm" :disabled="busy" @click="action(async () => { diagnostics = await portal('diagnostics', { run_id: run.id }) })">{{ words.diagnostics }}</button>
            <button v-if="run.result_path" class="btn sm" :disabled="busy" @click="download(run.id)">{{ words.download }}</button>
          </div>
        </article>
      </section>
      <section v-if="diagnostics" class="panel mb-6" data-testid="project-diagnostics" aria-live="polite">
        <h2>{{ words.diagnostics }}</h2><p class="help">{{ words.diagnosticsHelp }}</p>
        <p v-if="!diagnostics.length">{{ words.noLogs }}</p>
        <article v-for="(entry, index) in diagnostics" :key="index" class="mt-4">
          <p>{{ entry.kind }} · {{ statuses[entry.status] ?? entry.status }} · {{ entry.code }}</p><pre v-if="entry.log">{{ entry.log }}</pre>
        </article><button class="btn sm mt-3" @click="diagnostics = null">{{ words.close }}</button>
      </section>
      <p class="help mt-6">{{ pick('Model use is optional. Bring your own API; organizer credits are not provided. Never include a permanent key in your repository or ZIP.','模型调用可选，需要时请自备 API，平台不提供额度。不要把永久密钥放进仓库或 ZIP。') }}</p>
    </template>
  </section>
</template>

<style scoped>
h2 { font-size: 1.2rem; font-weight: 600; } h3 { font-weight: 600; }
.project-row { padding: 1rem 0; border-bottom: 1px solid #333; }
pre { max-height: 24rem; overflow: auto; padding: 1rem; margin-top: .5rem; background: #0b0b0b; font-size: .8rem; white-space: pre-wrap; overflow-wrap: anywhere; }
</style>
