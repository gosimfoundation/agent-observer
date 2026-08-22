<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'
import heroImage from '../../assets/images/cosmos-observatory-hero.jpg'

const { t, pick } = useI18n()
type Step = { label: string; date: string }
const pipeline = computed(() => t('hero.pipeline') as Step[])
</script>

<template>
  <section id="top" class="hero-section cosmos-hero poster-canvas">
    <div class="hero-media photo-wash" data-video-background aria-hidden="true">
      <!-- Replace this image with a muted autoplay video carrying class="hero-video". -->
      <img :src="heroImage" alt="" fetchpriority="high">
      <div class="hero-plasma plasma-field"></div>
      <div class="hero-plasma-secondary plasma-field"></div>
    </div>
    <div class="hero-overlay" aria-hidden="true"></div>

    <div class="relative z-10 mx-auto flex min-h-[calc(100svh-4rem)] max-w-[1440px] flex-col px-6 md:px-10 xl:px-14">
      <div class="hero-meta grid grid-cols-2 gap-4 border-b border-white/25 py-5 font-mono text-xs uppercase tracking-[.1em] text-white/60 md:grid-cols-4">
        <span>GOSIM / OPEN SURVEY</span>
        <span>{{ pick('Open call / 2026', '公开征集 / 2026') }}</span>
        <span class="hidden md:block">RA 00H 00M / DEC +00°</span>
        <span class="text-right text-[#315efb]">{{ pick('Registration coming soon', '报名即将开始') }}</span>
      </div>

      <div class="flex flex-1 flex-col justify-end py-12 md:py-16">
        <div class="mb-7 flex items-center gap-4 font-mono text-xs uppercase leading-relaxed tracking-[.12em] text-[#315efb] md:text-sm">
          <span class="h-2 w-2 bg-[#315efb]"></span>
          {{ t('hero.eyebrow') }}
        </div>

        <h1 class="hero-title distressed-type" :aria-label="t('hero.system')">{{ t('hero.system') }}</h1>

        <div class="mt-8 grid gap-8 border-t border-white/28 pt-7 md:grid-cols-[minmax(0,1fr)_auto] md:items-end">
          <div>
            <p class="max-w-2xl text-base leading-relaxed text-white/78 md:text-lg">{{ t('hero.lede') }}</p>
            <p class="mt-4 font-mono text-xs uppercase leading-[1.7] tracking-[.08em] text-[#315efb] md:text-sm">{{ t('hero.subtitle') }}</p>
          </div>
          <div class="flex flex-wrap gap-3 md:justify-end">
            <span aria-disabled="true" class="hero-action hero-action-primary pointer-events-none">
              {{ pick('Registration coming soon', '报名即将开始') }}
            </span>
            <router-link to="/brief" class="hero-action">
              {{ pick('Mission brief', '赛题简报') }} <span>→</span>
            </router-link>
          </div>
        </div>
      </div>

      <div class="hero-timeline grid grid-cols-3 border-t border-white/25">
        <div v-for="(step, index) in pipeline" :key="step.label" class="border-r border-white/18 py-5 last:border-r-0 md:py-6">
          <span class="font-mono text-xs text-[#315efb]">0{{ index + 1 }}</span>
          <p class="mt-2 text-sm font-semibold leading-snug">{{ step.label }}</p>
          <p class="mt-1 font-mono text-xs leading-snug tracking-[.04em] text-white/50">{{ step.date }}</p>
        </div>
      </div>
    </div>

    <div class="hero-side-note" aria-hidden="true">Human judgment / machine speed / one shared sky</div>
  </section>
</template>

<style scoped>
.cosmos-hero { min-height: 760px; background: #060607; }

.hero-media {
  position: absolute;
  z-index: 0;
  inset: 0;
}

.hero-media img {
  object-position: 56% center;
  animation: slow-pan 22s ease-in-out infinite alternate;
}

.hero-media :deep(.hero-video),
.hero-video { width: 100%; height: 100%; object-fit: cover; }

.hero-media::after {
  background:
    linear-gradient(90deg, rgba(6,6,7,.96) 0%, rgba(6,6,7,.82) 35%, rgba(6,6,7,.18) 67%, rgba(6,6,7,.36) 100%),
    linear-gradient(0deg, rgba(6,6,7,.9), transparent 54%);
}

.hero-overlay {
  position: absolute;
  z-index: 1;
  inset: 0;
  background:
    linear-gradient(90deg, transparent 49.8%, rgba(238,231,220,.1) 50%, transparent 50.2%),
    linear-gradient(180deg, transparent 74%, rgba(6,6,7,.42));
}

.hero-plasma { top: 12%; right: -5%; transform: rotate(-10deg); }
.hero-plasma-secondary {
  right: 16%;
  bottom: 4%;
  width: clamp(17rem, 34vw, 35rem);
  opacity: .6;
  transform: rotate(15deg);
  animation-delay: -7s;
}

.hero-title {
  display: block;
  max-width: 14ch;
  white-space: normal;
  color: #f5f5f5;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  font-size: clamp(3rem, 6.5vw, 6.75rem);
  font-weight: 600;
  letter-spacing: -.055em;
  line-height: 1.02;
  text-wrap: balance;
}

.hero-action {
  display: inline-flex;
  min-width: 11.5rem;
  align-items: center;
  justify-content: space-between;
  border: 1px solid rgba(238,231,220,.56);
  padding: .95rem 1rem;
  color: #f5f5f5;
  background: rgba(6,6,7,.42);
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  font-size: .875rem;
  letter-spacing: .13em;
  text-transform: uppercase;
  transition: color .2s ease, background .2s ease, border-color .2s ease;
}

.hero-action:hover { color: #000000; border-color: #f5f5f5; background: #f5f5f5; }
.hero-action-primary { color: #fff; border-color: #315efb; background: #315efb; }
.hero-action-primary:hover { border-color: #fff; background: #fff; }
.hero-timeline > div { padding-left: clamp(.5rem, 2vw, 1.5rem); }

.hero-side-note {
  position: absolute;
  z-index: 3;
  top: 50%;
  right: -8.4rem;
  color: rgba(255,255,255,.45);
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  font-size: .875rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  transform: rotate(90deg);
}

@media (max-width: 720px) {
  .cosmos-hero { min-height: 760px; }
  .hero-media img { object-position: 64% center; }
  .hero-media::after { background: linear-gradient(90deg, rgba(6,6,7,.9), rgba(6,6,7,.5)), linear-gradient(0deg, rgba(6,6,7,.92), transparent 60%); }
  .hero-plasma { top: 16%; right: -42%; }
  .hero-plasma-secondary { right: -15%; bottom: 12%; }
  .hero-title { max-width: 14ch; font-size: clamp(3rem, 6.5vw, 6.75rem); line-height: 1.02; }
  .hero-action { min-width: calc(50% - .4rem); }
  .hero-side-note { display: none; }
}
</style>
