<script setup lang="ts">
import { defineAsyncComponent, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from '../../composables/useI18n'
import { assetUrl } from '../../composables/api'
import { DEMO_REPLAY, loadDemoReplayFacts, loadDemoReplayPage, type DemoReplayFacts } from '../../lib/demoReplay'
import { num } from '../../lib/format'

/**
 * Official example on the home page: the same replay viewer the submission page uses, showing the
 * baseline agent's full run on a public practice scenario. Neither the viewer nor the ~330 KB replay is
 * fetched until the section comes near the viewport, so first paint is untouched.
 */
const ReplayViewer = defineAsyncComponent(() => import('../submissions/ReplayViewer.vue'))
const { t, tf } = useI18n()
const root = ref<HTMLElement | null>(null)
const near = ref(false)
const facts = ref<DemoReplayFacts | null>(null)
// Autoplay at 8× and loop; with reduced motion it loads paused on the first round.
const reduced = typeof window !== 'undefined' && !!window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
const playback = { speed: 8, loop: true, play: !reduced }
let observer: IntersectionObserver | undefined
const loadPage = () => loadDemoReplayPage(assetUrl(DEMO_REPLAY.page))

function wake() {
  if (near.value) return
  near.value = true
  observer?.disconnect()
  loadDemoReplayFacts(assetUrl(DEMO_REPLAY.facts)).then(f => { facts.value = f }).catch(() => { /* the caption falls back to its plain label */ })
}
onMounted(() => {
  if (!root.value) return
  if (typeof IntersectionObserver !== 'function') { wake(); return }
  observer = new IntersectionObserver(entries => { if (entries.some(e => e.isIntersecting)) wake() }, { rootMargin: '600px 0px' })
  observer.observe(root.value)
})
onUnmounted(() => observer?.disconnect())
</script>

<template>
  <section id="demo" ref="root" class="poster-section poster-canvas py-16 md:py-24" data-testid="demo-replay-section">
    <div class="mx-auto max-w-[1600px] px-5 md:px-10 xl:px-14">
      <span class="poster-kicker reveal">{{ t('home.demo.kicker') }}</span>
      <h2 class="demo-title reveal mt-6">{{ t('home.demo.title') }}</h2>
      <p class="demo-facts reveal mt-4" data-testid="demo-replay-facts">
        <template v-if="facts">{{ tf('home.demo.facts', { scenario: facts.scenario, seed: facts.seed, nights: facts.nights, rounds: num(facts.rounds, 0), score: num(facts.score, 2) }) }}</template>
        <template v-else>&nbsp;</template>
      </p>
      <div class="demo-frame mt-6">
        <ReplayViewer v-if="near" :source="loadPage" autoload :playback="playback" :note="t('home.demo.note')" />
        <div v-else class="demo-placeholder" aria-hidden="true"></div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.demo-title { max-width: 60rem; font-size: clamp(1.35rem, 2.6vw, 2.1rem); font-weight: 500; letter-spacing: -.03em; line-height: 1.2; color: #f5f5f5; }
.demo-facts { font-family: 'IBM Plex Mono', ui-monospace, monospace; font-size: .78rem; letter-spacing: .04em; color: #9aa4b8; overflow-wrap: anywhere; }
.demo-frame { min-width: 0; }
.demo-placeholder { height: 868px; border: 1px solid rgba(255,255,255,.12); background: #040915; }
</style>
