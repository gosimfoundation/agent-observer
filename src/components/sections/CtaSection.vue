<script setup lang="ts">
import { useI18n } from '../../composables/useI18n'
const { t, pick } = useI18n()
</script>

<template>
  <section class="bg-[#2b2350] py-20 text-white md:py-28">
    <div class="reveal mx-auto grid max-w-[1440px] gap-10 px-6 md:px-10 lg:grid-cols-[1fr_auto] lg:items-end xl:px-14">
      <div>
        <span class="font-mono text-xs uppercase tracking-[.12em]">{{ pick('2026 / GOSIM / AGENTIC COSMOS', '2026 / GOSIM / 智能宇宙') }}</span>
        <h2 class="mt-8 max-w-[14ch] text-[clamp(2.25rem,5vw,4.75rem)] font-semibold leading-[1.14] tracking-[-.045em]">{{ t('cta.title') }}</h2>
        <p class="mt-8 max-w-2xl text-base font-medium leading-relaxed md:text-xl">{{ t('cta.tagline') }}</p>
        <p class="mono-label mt-4 text-white/70">{{ t('cta.location') }}</p>
      </div>
    </div>
  </section>
</template>
