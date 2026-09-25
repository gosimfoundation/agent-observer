<script setup lang="ts">
// Mid-Autumn Festival greeting: shown on the festival day, dismissible, remembered per year.
import { onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from '../../composables/useI18n'
import { isMidAutumnToday } from '../../lib/eggs'

const { t } = useI18n()
const storageKey = `egg-mid-autumn-${new Date().getFullYear()}`
const visible = ref(false)
const parade = ref(0)
const moonMap = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined

/** Orthographic view of the near side, north up, selenographic east to the right. */
function project(lat: number, lon: number) {
  const r = Math.PI / 180
  return { x: Math.cos(lat * r) * Math.sin(lon * r), y: -Math.sin(lat * r) }
}
/** The main maria (latitude, longitude, radius in km) so the disk reads as the Moon. */
const MARIA = ([
  [32.8, -15.6, 560], [28.0, 17.5, 350], [8.5, 31.4, 440], [17.0, 59.1, 280], [20.7, -56.7, 700],
  [-21.3, -16.6, 350], [-7.8, 51.3, 420], [-15.2, 35.5, 170], [-24.4, -38.6, 190],
] as const).map(([lat, lon, km]) => {
  const { x, y } = project(lat, lon)
  const size = km / 1737
  return { x, y, rx: size * Math.cos(lon * Math.PI / 180), ry: size * Math.cos(lat * Math.PI / 180) }
})
/** Chang'e 3 landing site, where the Yutu rover stopped (44.12°N, 19.51°W). */
const YUTU = project(44.12, -19.51)

onMounted(() => {
  // Automated browsers (tests, screenshot tours) only see it when asked for with ?egg=midautumn.
  const forced = new URLSearchParams(window.location.search).get('egg') === 'midautumn'
  if (!forced && (navigator.webdriver || !isMidAutumnToday())) return
  try { if (localStorage.getItem(storageKey) === 'closed') return } catch { /* storage may be blocked */ }
  visible.value = true
})
onUnmounted(() => { if (timer) clearTimeout(timer) })

function close() {
  visible.value = false
  try { localStorage.setItem(storageKey, 'closed') } catch { /* storage may be blocked */ }
}

/** A jade rabbit hops across the page while mooncakes and lanterns drift up. */
function releaseRabbit() {
  parade.value += 1
  moonMap.value = true
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => { parade.value = 0 }, 4200)
}
</script>

<template>
  <div v-if="visible" class="mid-autumn" role="status" data-testid="mid-autumn-egg">
    <span class="mid-autumn-moon" aria-hidden="true"></span>
    <p class="mid-autumn-text">
      <strong>{{ t('eggs.mid_autumn.title') }}</strong>
      <span>{{ t('eggs.mid_autumn.body') }}</span>
    </p>
    <button type="button" class="mid-autumn-action" data-testid="mid-autumn-rabbit" @click="releaseRabbit">
      {{ t('eggs.mid_autumn.rabbit') }}
    </button>
    <button type="button" class="mid-autumn-close" :aria-label="t('eggs.mid_autumn.close')" @click="close">×</button>
    <div v-if="moonMap" class="mid-autumn-yutu" data-testid="mid-autumn-yutu">
      <svg viewBox="-1.12 -1.12 2.24 2.24" role="img" :aria-label="t('eggs.mid_autumn.map_label')">
        <defs>
          <radialGradient id="mid-autumn-disk" cx="42%" cy="38%" r="72%">
            <stop offset="0" stop-color="#fffbe8" /><stop offset=".62" stop-color="#efdcaa" /><stop offset="1" stop-color="#c7ad70" />
          </radialGradient>
        </defs>
        <circle r="1" fill="url(#mid-autumn-disk)" />
        <ellipse v-for="(m, i) in MARIA" :key="i" :cx="m.x" :cy="m.y" :rx="m.rx" :ry="m.ry" fill="rgba(98, 86, 64, .42)" />
        <circle class="mid-autumn-ping" :cx="YUTU.x" :cy="YUTU.y" r=".13" />
        <circle :cx="YUTU.x" :cy="YUTU.y" r=".065" fill="#ff4a3d" stroke="#fff3e0" stroke-width=".02" />
      </svg>
      <p>
        <strong>{{ t('eggs.mid_autumn.yutu_title') }}</strong>
        <span>{{ t('eggs.mid_autumn.yutu_body') }}</span>
      </p>
    </div>
  </div>
  <div v-if="parade" :key="parade" class="mid-autumn-parade" aria-hidden="true">
    <span class="mid-autumn-rabbit">🐇</span>
    <span v-for="i in 9" :key="i" class="mid-autumn-float"
      :style="{ left: `${6 + i * 9.5}%`, animationDelay: `${(i % 4) * 0.18}s` }">{{ i % 3 === 0 ? '🏮' : '🥮' }}</span>
  </div>
</template>

<style scoped>
.mid-autumn {
  position: fixed; top: 76px; left: 50%; transform: translateX(-50%); z-index: 60;
  display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: .5rem .9rem;
  width: min(720px, calc(100vw - 24px)); padding: .8rem 2.6rem .8rem 1rem;
  border: 1px solid rgba(255, 214, 128, .45); border-radius: 12px;
  background: linear-gradient(135deg, rgba(40, 24, 8, .96), rgba(10, 12, 28, .96));
  color: #fff4dc; box-shadow: 0 12px 40px rgba(0, 0, 0, .45), 0 0 32px rgba(255, 200, 90, .18);
  animation: mid-autumn-in .45s ease-out;
}
/* Drawn with CSS so it glows the same on devices without colour emoji fonts. */
.mid-autumn-moon {
  width: 2.3rem; height: 2.3rem; border-radius: 50%;
  background: radial-gradient(circle at 38% 36%, #fffbe8 0 18%, #ffe7a3 45%, #f5c35c 100%);
  box-shadow: 0 0 18px 4px rgba(255, 214, 120, .55), inset -4px -5px 0 rgba(214, 150, 50, .25);
}
.mid-autumn-text { display: flex; flex-direction: column; gap: .15rem; margin: 0; font-size: .9rem; line-height: 1.5; }
.mid-autumn-text strong { color: #ffd98a; font-size: 1rem; }
.mid-autumn-action {
  flex-shrink: 0; padding: .45rem .8rem; border: 1px solid rgba(255, 214, 128, .6); border-radius: 999px;
  background: rgba(255, 214, 128, .12); color: #ffe3a8; font-size: .82rem; cursor: pointer; white-space: nowrap;
}
.mid-autumn-action:hover { background: rgba(255, 214, 128, .24); }
.mid-autumn-close {
  position: absolute; top: .35rem; right: .55rem; border: 0; background: none;
  color: rgba(255, 244, 220, .7); font-size: 1.3rem; line-height: 1; cursor: pointer;
}
.mid-autumn-close:hover { color: #fff; }
.mid-autumn-parade { position: fixed; inset: 0; z-index: 90; pointer-events: none; overflow: hidden; }
.mid-autumn-rabbit {
  position: absolute; bottom: 8vh; left: -10vw; font-size: 3rem;
  animation: mid-autumn-hop 3.6s cubic-bezier(.4, 0, .6, 1) forwards;
}
.mid-autumn-float {
  position: absolute; bottom: -3rem; font-size: 1.8rem; opacity: 0;
  animation: mid-autumn-rise 3.4s ease-out forwards;
}
.mid-autumn-yutu {
  grid-column: 1 / -1; display: flex; align-items: center; gap: 1rem;
  margin-top: .35rem; padding-top: .75rem; border-top: 1px solid rgba(255, 214, 128, .25);
  animation: mid-autumn-fade .5s ease-out;
}
.mid-autumn-yutu svg { flex-shrink: 0; width: 118px; height: 118px; filter: drop-shadow(0 0 14px rgba(255, 214, 120, .35)); }
.mid-autumn-yutu p { display: flex; flex-direction: column; gap: .3rem; margin: 0; font-size: .84rem; line-height: 1.6; color: #f6ead0; }
.mid-autumn-yutu strong { color: #ffd98a; font-size: .95rem; }
.mid-autumn-ping { fill: none; stroke: #ff7a70; stroke-width: .03; transform-box: fill-box; transform-origin: center; animation: mid-autumn-ping 1.8s ease-out infinite; }
@keyframes mid-autumn-fade { from { opacity: 0; } to { opacity: 1; } }
@keyframes mid-autumn-ping { from { transform: scale(.6); opacity: 1; } to { transform: scale(2.2); opacity: 0; } }
@keyframes mid-autumn-in { from { opacity: 0; transform: translate(-50%, -12px); } to { opacity: 1; transform: translate(-50%, 0); } }
@keyframes mid-autumn-hop {
  0% { transform: translate(0, 0); }
  12% { transform: translate(14vw, -9vh); } 25% { transform: translate(28vw, 0); }
  37% { transform: translate(42vw, -9vh); } 50% { transform: translate(56vw, 0); }
  62% { transform: translate(70vw, -9vh); } 75% { transform: translate(84vw, 0); }
  87% { transform: translate(98vw, -9vh); } 100% { transform: translate(120vw, 0); }
}
@keyframes mid-autumn-rise {
  0% { transform: translateY(0) scale(.8); opacity: 0; }
  15% { opacity: 1; }
  100% { transform: translateY(-75vh) scale(1.1); opacity: 0; }
}
@media (max-width: 640px) {
  .mid-autumn { top: 68px; grid-template-columns: auto 1fr; padding: .7rem 2.2rem .7rem .8rem; font-size: .85rem; }
  .mid-autumn-moon { grid-row: span 2; width: 1.9rem; height: 1.9rem; align-self: start; }
  .mid-autumn-text { font-size: .82rem; }
  .mid-autumn-action { justify-self: start; padding: .35rem .7rem; font-size: .78rem; }
  .mid-autumn-yutu { gap: .7rem; }
  .mid-autumn-yutu svg { width: 84px; height: 84px; }
  .mid-autumn-yutu p { font-size: .78rem; }
}
@media (prefers-reduced-motion: reduce) {
  .mid-autumn { animation: none; }
  .mid-autumn-parade { display: none; }
  .mid-autumn-yutu, .mid-autumn-ping { animation: none; }
}
</style>
