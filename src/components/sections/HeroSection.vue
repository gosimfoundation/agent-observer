<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'

const { t } = useI18n()
const locationLines = computed(() => t('hero.location') as string[])
type Step = { label: string; date: string }
const pipeline = computed(() => t('hero.pipeline') as Step[])
</script>

<template>
  <section id="top" class="relative min-h-[720px] overflow-hidden bg-[#080a10] text-white">
    <div class="starfield absolute inset-0"></div>
    <div class="absolute inset-0 bg-gradient-to-b from-[#0a0e1a]/40 via-transparent to-[#080a10]"></div>

    <div class="relative z-10 mx-auto flex min-h-[720px] max-w-[1440px] flex-col px-6 md:px-10 xl:px-14">
      <div class="flex flex-1 items-center pt-28 pb-10">
        <div class="w-full max-w-5xl">
          <div class="mb-7 flex items-center gap-4 font-mono text-xs uppercase tracking-[.12em] text-white/70 md:text-sm">
            <span class="h-2 w-2 bg-accent"></span>
            <span>{{ t('hero.eyebrow') }}</span>
          </div>

          <h1 class="max-w-[16ch] text-balance text-[clamp(2.6rem,6vw,5.6rem)] font-semibold leading-[1.06] tracking-[-.05em]">
            {{ t('hero.system') }}
          </h1>
          <p class="mt-4 font-mono text-sm uppercase tracking-[.14em] text-accent md:text-base">{{ t('hero.subtitle') }}</p>

          <p class="mt-9 max-w-2xl border-t border-white/30 pt-6 text-base leading-relaxed text-white/85 md:text-xl">
            {{ t('hero.lede') }}
          </p>

          <div class="mt-8 font-mono text-[11px] uppercase tracking-[.14em] text-white/60 md:text-xs">
            <p v-for="line in locationLines" :key="line" class="mt-1 first:mt-0">{{ line }}</p>
          </div>

          <span class="mt-9 inline-flex items-center border border-white/45 px-6 py-4 font-mono text-[11px] uppercase tracking-[.14em] text-white/75">
            {{ t('hero.cta') }}
          </span>
        </div>
      </div>

      <div class="border-t border-white/25 py-7">
        <div class="flex flex-wrap items-center gap-x-10 gap-y-4">
          <div v-for="(step, i) in pipeline" :key="step.label" class="flex items-center gap-10">
            <div>
              <div class="text-sm font-medium">{{ step.label }}</div>
              <div class="mt-1 font-mono text-[11px] tracking-[.1em] text-white/55">{{ step.date }}</div>
            </div>
            <span v-if="i < pipeline.length - 1" class="text-white/30">→</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* 星场：两层不同密度的点，纯 CSS，无外部资源 */
.starfield {
  background-color: #080a10;
  background-image:
    radial-gradient(1px 1px at 12% 22%, rgba(255,255,255,.85) 50%, transparent 50%),
    radial-gradient(1px 1px at 34% 68%, rgba(255,255,255,.55) 50%, transparent 50%),
    radial-gradient(1.5px 1.5px at 58% 18%, rgba(255,255,255,.9) 50%, transparent 50%),
    radial-gradient(1px 1px at 74% 52%, rgba(255,255,255,.5) 50%, transparent 50%),
    radial-gradient(1px 1px at 88% 78%, rgba(255,255,255,.7) 50%, transparent 50%),
    radial-gradient(1.5px 1.5px at 22% 84%, rgba(255,255,255,.6) 50%, transparent 50%),
    radial-gradient(1px 1px at 46% 38%, rgba(255,255,255,.45) 50%, transparent 50%),
    radial-gradient(circle at 70% 30%, rgba(120,110,190,.18), transparent 55%),
    radial-gradient(circle at 20% 70%, rgba(90,130,170,.14), transparent 55%);
  background-size: 320px 320px, 320px 320px, 460px 460px, 460px 460px, 620px 620px, 620px 620px, 240px 240px, 100% 100%, 100% 100%;
}
</style>
