<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'
import { assetUrl } from '../../composables/api'

const { t, pick, locale } = useI18n()
type Step = { label: string; date: string }
const pipeline = computed(() => t('hero.pipeline') as Step[])
const heroTitleLines = computed(() => locale.value === 'zh' ? ['智能体巡天', '黑客松'] : [t('hero.system')])
</script>

<template>
  <section id="top" class="hero-section cosmos-hero poster-canvas">
    <div class="hero-media" aria-hidden="true">
      <video autoplay loop muted playsinline preload="auto" :poster="assetUrl('/media/survey-milky-way.png')">
        <source :src="assetUrl('/media/survey-night-sky.mp4')" type="video/mp4">
      </video>
    </div>
    <div class="hero-overlay" aria-hidden="true"></div>

    <div class="hero-layout relative z-10 mx-auto flex min-h-[calc(100svh-4rem)] max-w-[1600px] flex-col px-5 md:px-10 xl:px-14">
      <div class="hero-meta grid grid-cols-2 gap-4 border-b border-white/20 py-5 font-mono text-xs uppercase tracking-[.1em] text-white/60 md:grid-cols-4">
        <span>GOSIM / OPEN SURVEY</span>
        <span>{{ pick('Open call / 2026', '公开征集 / 2026') }}</span>
        <span class="hidden md:block">RA 18H 36M / DEC +38°</span>
        <span class="text-right text-[#78a6ff]">{{ pick('Registration coming soon', '报名即将开始') }}</span>
      </div>

      <div class="hero-stage flex flex-1 items-center py-10">
        <div class="hero-copy">
          <div class="hero-kicker mb-7 flex items-center gap-4 font-mono text-xs uppercase leading-relaxed tracking-[.12em] text-[#78a6ff] md:text-sm">
            <span class="live-dot h-2 w-2 bg-[#78a6ff]"></span>
            {{ t('hero.eyebrow') }}
          </div>

          <h1 class="hero-title" :class="{ 'hero-title-zh': locale === 'zh' }" :aria-label="t('hero.system')">
            <span v-for="line in heroTitleLines" :key="line" class="hero-title-line">{{ line }}</span>
          </h1>
          <p class="hero-subtitle mt-4 font-mono text-sm uppercase tracking-[.22em] text-[#78a6ff] md:text-base">{{ t('hero.subtitle') }}</p>

          <div class="hero-intro mt-8 max-w-3xl border-t border-white/25 pt-6">
            <p class="text-base leading-[1.75] text-white/82 md:text-lg">{{ t('hero.lede') }}</p>
            <div class="mt-7 flex flex-wrap gap-3">
              <span aria-disabled="true" class="hero-action hero-action-primary pointer-events-none">
                {{ pick('Registration coming soon', '报名即将开始') }}
              </span>
              <router-link to="/brief" class="hero-action">
                {{ pick('Mission brief', '赛题简报') }} <span>→</span>
              </router-link>
            </div>
          </div>
        </div>

      </div>

      <div class="hero-timeline grid grid-cols-3 border-t border-white/22">
        <div v-for="(step, index) in pipeline" :key="step.label" class="border-r border-white/16 py-5 last:border-r-0 md:py-6">
          <span class="font-mono text-xs text-[#78a6ff]">0{{ index + 1 }}</span>
          <p class="mt-2 text-sm font-semibold leading-snug">{{ step.label }}</p>
          <p class="mt-1 font-mono text-xs leading-snug tracking-[.04em] text-white/50">{{ step.date }}</p>
        </div>
      </div>
    </div>

    <div class="hero-side-note" aria-hidden="true">Human judgment / machine speed / one shared sky</div>
  </section>
</template>

<style scoped>
.cosmos-hero {
  min-height: 760px;
  color: #f7f9ff;
  background: #02050c;
}

.hero-media {
  position: absolute;
  z-index: 0;
  inset: 0;
}

.hero-media video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center bottom;
  filter: saturate(1.16) contrast(1.06) brightness(.94);
}

.hero-media::after {
  position: absolute;
  inset: 0;
  content: '';
  background:
    linear-gradient(90deg, rgba(2,5,14,.9) 0%, rgba(3,10,25,.62) 42%, rgba(2,6,16,.12) 76%, rgba(2,5,14,.24) 100%),
    linear-gradient(0deg, rgba(2,5,14,.72) 0%, rgba(2,5,14,.1) 54%, rgba(2,5,14,.3) 100%);
}

.hero-overlay {
  position: absolute;
  z-index: 1;
  inset: 0;
  pointer-events: none;
  background:
    radial-gradient(circle at 62% 34%, rgba(70,126,255,.1), transparent 27%),
    linear-gradient(180deg, transparent 72%, rgba(2,5,14,.4));
}

.hero-layout { min-height: max(760px, calc(100svh - 4rem)); }
.hero-copy { max-width: 850px; }

.hero-title {
  max-width: 11ch;
  color: #f7f9ff;
  font-family: 'Space Grotesk', 'Noto Sans SC', system-ui, sans-serif;
  font-size: clamp(4rem, 7.6vw, 8rem);
  font-weight: 600;
  letter-spacing: -.065em;
  line-height: .92;
  text-wrap: balance;
}

.hero-title-line { display: block; }
.hero-title-zh {
  font-size: clamp(3.6rem, 6.6vw, 7rem);
  line-height: 1.04;
  letter-spacing: -.065em;
}
.hero-title-zh + .hero-subtitle { margin-top: 1.5rem; }

.hero-action {
  display: inline-flex;
  min-width: 11.5rem;
  min-height: 48px;
  align-items: center;
  justify-content: space-between;
  border: 1px solid rgba(217,229,255,.48);
  padding: .8rem 1rem;
  color: #f7f9ff;
  background: rgba(2,8,20,.46);
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  font-size: .75rem;
  letter-spacing: .11em;
  text-transform: uppercase;
  transition: color .2s ease, background .2s ease, border-color .2s ease;
}

.hero-action:hover { color: #06102a; border-color: #f7f9ff; background: #f7f9ff; }
.hero-action-primary { color: #ffffff; border-color: #315efb; background: #315efb; }
.hero-timeline > div { padding-left: clamp(.65rem, 2vw, 1.5rem); }

.hero-side-note {
  position: absolute;
  z-index: 3;
  top: 50%;
  right: -8.4rem;
  color: rgba(255,255,255,.4);
  font-family: 'IBM Plex Mono', ui-monospace, monospace;
  font-size: .75rem;
  letter-spacing: .18em;
  text-transform: uppercase;
  transform: rotate(90deg);
}

@media (max-width: 1023px) {
  .hero-stage { align-items: end; }
  .hero-title { max-width: 12ch; font-size: clamp(3.8rem, 12vw, 7rem); }
  .hero-side-note { display: none; }
}

@media (max-width: 720px) {
  .cosmos-hero { min-height: 900px; }
  .hero-layout { min-height: 900px; }
  .hero-media video { object-position: center bottom; }
  .hero-media::after {
    background:
      linear-gradient(90deg, rgba(2,5,14,.82), rgba(2,7,18,.28)),
      linear-gradient(0deg, rgba(2,5,14,.78), transparent 58%, rgba(2,5,14,.34));
  }
  .hero-stage { gap: 2rem; padding-top: 2rem; }
  .hero-title { font-size: clamp(3.6rem, 18vw, 5.5rem); }
  .hero-title-zh { font-size: clamp(3.15rem, 16vw, 4.75rem); line-height: 1.04; }
  .hero-intro { margin-top: 1.5rem; padding-top: 1.25rem; }
  .hero-action { min-width: calc(50% - .4rem); }
}
</style>
