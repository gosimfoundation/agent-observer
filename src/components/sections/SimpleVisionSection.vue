<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'

const { t } = useI18n()

type Stat = { value: string; label: string }
const stats = computed(() => t('home.vision.stats') as Stat[])
</script>

<template>
  <section id="about" class="bg-bg-primary py-24 md:py-36">
    <div class="mx-auto max-w-[1440px] px-6 md:px-10 xl:px-14">
      <div class="grid gap-12 lg:grid-cols-2 lg:gap-20">
        <div class="reveal">
          <span class="section-kicker">{{ t('home.vision.kicker') }}</span>
          <h2 class="section-title mt-8">{{ t('home.vision.title') }}</h2>
          <p class="mt-6 text-lg font-medium leading-relaxed text-text-primary md:text-xl">
            {{ t('home.vision.lede') }}
          </p>
        </div>

        <div class="reveal reveal-delay-1 flex flex-col justify-between">
          <div class="space-y-5 text-base leading-relaxed text-text-secondary md:text-lg">
            <p v-for="(paragraph, index) in t('home.vision.paragraphs')" :key="index">
              {{ paragraph }}
            </p>
          </div>

          <div class="mt-10 flex flex-wrap gap-10 border-t border-border pt-8">
            <div v-for="stat in stats" :key="stat.label">
              <div class="text-3xl font-semibold tracking-[-.03em] text-accent md:text-4xl">{{ stat.value }}</div>
              <div class="mt-1 font-mono text-[10px] uppercase tracking-[.12em] text-text-tertiary">{{ stat.label }}</div>
            </div>
          </div>

          <router-link
            to="/vision"
            class="mt-10 inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[.12em] text-accent transition-colors hover:text-accent-hover"
          >
            {{ t('home.vision.link') }}
            <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M5 12h14m-7-7 7 7-7 7"/></svg>
          </router-link>
        </div>
      </div>
    </div>
  </section>
</template>
