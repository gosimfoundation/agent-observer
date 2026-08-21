<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'

const { t } = useI18n()

type Step = { n: string; title: string; desc: string }
type TimelineItem = { label: string; desc: string }
const steps = computed(() => t('home.participate.steps') as Step[])
const timeline = computed(() => t('home.participate.timeline') as TimelineItem[])
</script>

<template>
  <section id="participate" class="bg-bg-primary py-24 md:py-36">
    <div class="mx-auto max-w-[1440px] px-6 md:px-10 xl:px-14">
      <div class="grid gap-12 lg:grid-cols-[.8fr_1.2fr] lg:gap-20">
        <div class="reveal lg:sticky lg:top-28 lg:self-start">
          <span class="section-kicker">{{ t('home.participate.kicker') }}</span>
          <h2 class="section-title mt-8">{{ t('home.participate.title') }}</h2>
          <p class="mt-6 text-lg leading-relaxed text-text-secondary md:text-xl">{{ t('home.participate.lede') }}</p>

          <div class="mt-10 hidden flex-wrap gap-8 border-t border-border pt-8 lg:flex">
            <div v-for="item in timeline" :key="item.label">
              <div class="text-base font-medium text-text-primary">{{ item.label }}</div>
              <div class="mt-1 font-mono text-[10px] uppercase tracking-[.1em] text-text-tertiary">{{ item.desc }}</div>
            </div>
          </div>
        </div>

        <div class="space-y-6">
          <div
            v-for="(step, index) in steps"
            :key="step.n"
            class="reveal border border-border bg-bg-secondary p-6 md:p-8"
            :class="`reveal-delay-${index + 1}`"
          >
            <div class="flex items-start gap-5">
              <span class="mono-label text-accent">{{ step.n }}</span>
              <div>
                <h3 class="text-lg font-medium text-text-primary md:text-xl">{{ step.title }}</h3>
                <p class="mt-2 text-sm leading-relaxed text-text-secondary md:text-base">{{ step.desc }}</p>
              </div>
            </div>
          </div>

          <div class="reveal reveal-delay-4 lg:hidden">
            <div class="mt-6 grid grid-cols-3 gap-4 border-t border-border pt-6">
              <div v-for="item in timeline" :key="item.label">
                <div class="text-sm font-medium text-text-primary">{{ item.label }}</div>
                <div class="mt-1 text-[10px] text-text-tertiary">{{ item.desc }}</div>
              </div>
            </div>
          </div>

          <div class="reveal reveal-delay-4 pt-4">
            <router-link
              to="/register"
              class="inline-block border border-accent px-6 py-3 font-mono text-[11px] uppercase tracking-[.12em] text-accent transition-colors hover:bg-accent hover:text-btn-text"
            >
              {{ t('home.participate.cta') }}
            </router-link>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>
