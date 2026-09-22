import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { execFileSync } from 'node:child_process'
import { createHash } from 'node:crypto'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = dirname(dirname(fileURLToPath(import.meta.url)))
const config = JSON.parse(readFileSync(join(root, 'site.config.json'), 'utf8'))
const output = join(root, '.site')
const release = join(root, 'release')
const origin = 'https://create.gosim.org'
const revision = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: root, encoding: 'utf8' }).trim()
const appBase = config.platform ? `${config.basePath}platform/` : config.basePath
function build(directory, basePath, extra = {}) {
  execFileSync('npm', ['run', 'build'], { cwd: join(root, directory), stdio: 'inherit', env: {
    ...process.env, VITE_BASE_PATH: basePath, VITE_SITE_URL: `${origin}${basePath.replace(/\/$/, '')}`, ...extra,
  } })
}
if (config.slug !== 'agenticapp26') {
  const url = process.env.VITE_SUPABASE_URL || ''
  const key = process.env.VITE_SUPABASE_ANON_KEY || ''
  let role
  try { role = JSON.parse(Buffer.from(key.split('.')[1], 'base64url').toString()).role } catch {}
  if (!/^https:\/\/[a-z0-9]+\.supabase\.co$/.test(url) || !(role === 'anon' || key.startsWith('sb_publishable_'))) {
    throw new Error('A public Supabase URL and anon/publishable key are required; administrative keys are never accepted')
  }
}
rmSync(output, { recursive: true, force: true })
rmSync(release, { recursive: true, force: true })
mkdirSync(output, { recursive: true })
mkdirSync(release, { recursive: true })
if (config.platform) {
  build('legacy-event', config.basePath, { VITE_AGENT_OBSERVER_URL: `${origin}${appBase}` })
  cpSync(join(root, 'legacy-event/dist'), output, { recursive: true })
}
build(config.appDirectory, appBase)
const destination = config.platform ? join(output, 'platform') : output
cpSync(join(root, config.appDirectory, 'dist'), destination, { recursive: true })
if (config.platform) {
  cpSync(join(root, 'scripts/platform-restore.js'), join(destination, 'restore-route.js'))
  const index = join(destination, 'index.html')
  writeFileSync(index, readFileSync(index, 'utf8').replace('<head>', `<head>\n<script src="${appBase}restore-route.js"></script>`))
  writeFileSync(join(destination, 'deployment.json'), JSON.stringify({ repository: `https://github.com/${config.repository}.git`, revision }))
  writeFileSync(join(output, 'index.html'), `<!doctype html>
<html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>巡天智能体 · Agent Observer</title><link rel="icon" href="${appBase}favicon.svg">
<script>window.location.replace('${appBase}' + window.location.search + window.location.hash)</script>
<meta http-equiv="refresh" content="0; url=${appBase}"></head><body><a href="${appBase}">巡天智能体 · Agent Observer</a></body></html>\n`)
}
const requiredFiles = config.platform ? ['index.html', 'platform/index.html', 'platform/restore-route.js', 'platform/deployment.json'] : ['index.html']
for (const file of requiredFiles) if (!existsSync(join(output, file))) throw new Error(`Missing ${file}`)
const manifest = { schemaVersion: 1, slug: config.slug, basePath: config.basePath, repository: config.repository,
  revision, supabaseUrl: process.env.VITE_SUPABASE_URL || '', requiredFiles }
writeFileSync(join(output, 'site-manifest.json'), JSON.stringify(manifest, null, 2) + '\n')
execFileSync('tar', ['-czf', join(release, 'site.tar.gz'), '-C', output, '.'])
const digest = createHash('sha256').update(readFileSync(join(release, 'site.tar.gz'))).digest('hex')
writeFileSync(join(release, 'site.tar.gz.sha256'), `${digest}  site.tar.gz\n`)
console.log(`Packaged ${config.slug} at ${revision}`)
