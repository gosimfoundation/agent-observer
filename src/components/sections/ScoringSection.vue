<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'
const { t } = useI18n()
const principles = computed(() => t('scoring.principles') as { term: string; desc: string }[])
const viz = computed(() => t('scoring.viz') as string[])
</script>

<template>
  <section id="scoring" class="bg-bg-primary py-24 md:py-36">
    <div class="mx-auto max-w-[1440px] px-6 md:px-10 xl:px-14">
      <div class="grid gap-10 lg:grid-cols-[.85fr_1.15fr] lg:gap-20">
        <div class="reveal">
          <span class="section-kicker">{{ t('scoring.kicker') }}</span>
          <h2 class="section-title mt-8">{{ t('scoring.title') }}</h2>
        </div>
        <div class="reveal reveal-delay-1">
          <p class="text-sm leading-relaxed text-text-secondary md:text-base">{{ t('scoring.intro') }}</p>
          <pre class="code-block mt-7"><code>{{ t('scoring.formula') }}</code></pre>
        </div>
      </div>

      <div class="reveal mt-20 border-t border-border pt-12">
        <h3 class="text-xl font-semibold tracking-[-.03em] text-text-primary md:text-2xl">{{ t('scoring.principlesTitle') }}</h3>
        <dl class="mt-8 grid gap-x-10 gap-y-7 md:grid-cols-2 lg:grid-cols-3">
          <div v-for="p in principles" :key="p.term" class="border-t border-border-subtle pt-4">
            <dt class="text-base font-medium text-text-primary">{{ p.term }}</dt>
            <dd class="mt-2 text-sm leading-relaxed text-text-secondary">{{ p.desc }}</dd>
          </div>
        </dl>
        <p class="mt-8 max-w-4xl text-sm leading-relaxed text-text-secondary md:text-base">{{ t('scoring.principlesClosing') }}</p>
      </div>

      <div class="reveal mt-20 border-t border-border pt-12">
        <h3 class="text-xl font-semibold tracking-[-.03em] text-text-primary md:text-2xl">{{ t('scoring.vizTitle') }}</h3>
        <div class="mt-6 max-w-4xl space-y-4">
          <p v-for="line in viz" :key="line" class="text-sm leading-relaxed text-text-secondary md:text-base">{{ line }}</p>
        </div>
        <p class="mono-label mt-6 text-text-muted">{{ t('scoring.vizNote') }}</p>
      </div>
    </div>
  </section>
</template>
