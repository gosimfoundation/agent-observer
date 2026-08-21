<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../composables/useI18n'
import { useScrollReveal } from '../composables/useScrollReveal'

useScrollReveal()
const { t, pick } = useI18n()

type Section = {
  kicker: string
  title: string
  paragraphs: string[]
  highlight?: string
  duties?: { n: string; title: string; desc: string }[]
  loopTitle?: string
  loop?: { stage: string; items: string[] }[]
  starterCode?: string
  archCode?: string
  formula?: string
  actionCode?: string
  rounds?: { number: string; name: string; dates: string; format: string; challenge: string; participants: string }[]
}

const sections = computed(() => t('vision.sections') as Section[])
</script>

<template>
  <main class="min-h-screen bg-bg-primary pb-24">
    <div class="border-b border-border-subtle">
      <div class="mx-auto max-w-[1440px] px-6 py-16 md:px-10 md:py-24 xl:px-14">
        <div class="reveal mx-auto max-w-3xl">
          <router-link
            to="/"
            class="inline-flex items-center gap-2 font-mono text-[10px] uppercase tracking-[.12em] text-text-tertiary transition-colors hover:text-accent"
          >
            <svg class="h-3 w-3" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M19 12H5m7 7-7-7 7-7"/></svg>
            {{ t('vision.backToHome') }}
          </router-link>
          <h1 class="mt-8 text-4xl font-semibold tracking-[-.04em] text-text-primary md:text-6xl">
            {{ t('vision.pageTitle') }}
          </h1>
          <p class="mt-4 text-lg text-text-secondary md:text-xl">{{ t('vision.pageSubtitle') }}</p>
          <p class="mt-8 text-base leading-relaxed text-text-secondary md:text-lg">{{ t('vision.intro') }}</p>
        </div>
      </div>
    </div>

    <article class="mx-auto max-w-3xl px-6 pt-16 md:px-10 md:pt-24 xl:px-14">
      <section
        v-for="(section, index) in sections"
        :key="index"
        class="reveal mb-20 scroll-mt-24 md:mb-28"
        :id="`section-${index + 1}`"
      >
        <span class="section-kicker">{{ section.kicker }}</span>
        <h2 class="mt-6 text-2xl font-semibold tracking-[-.03em] text-text-primary md:text-4xl">
          {{ section.title }}
        </h2>

        <div class="mt-8 space-y-5 text-base leading-relaxed text-text-secondary md:text-lg">
          <p v-for="(paragraph, pIndex) in section.paragraphs" :key="pIndex">{{ paragraph }}</p>
        </div>

        <blockquote
          v-if="section.highlight"
          class="mt-8 border-l-2 border-accent bg-bg-secondary p-6 text-base leading-relaxed text-text-primary md:text-lg"
        >
          {{ section.highlight }}
        </blockquote>

        <div v-if="section.duties" class="mt-10">
          <div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <div
              v-for="duty in section.duties"
              :key="duty.n"
              class="border border-border bg-bg-secondary p-5"
            >
              <span class="mono-label text-accent">{{ duty.n }}</span>
              <h3 class="mt-3 text-base font-medium text-text-primary">{{ duty.title }}</h3>
              <p class="mt-2 text-sm leading-relaxed text-text-secondary">{{ duty.desc }}</p>
            </div>
          </div>
        </div>

        <div v-if="section.loop" class="mt-10">
          <h3 class="text-base font-medium text-text-primary md:text-lg">{{ section.loopTitle }}</h3>
          <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
            <div
              v-for="stage in section.loop"
              :key="stage.stage"
              class="border border-border bg-bg-secondary p-4"
            >
              <h4 class="font-mono text-[10px] uppercase tracking-[.12em] text-accent">{{ stage.stage }}</h4>
              <ul class="mt-3 space-y-1 text-sm text-text-secondary">
                <li v-for="item in stage.items" :key="item">{{ item }}</li>
              </ul>
            </div>
          </div>
        </div>

        <div v-if="section.starterCode" class="mt-10">
          <pre class="code-block">{{ section.starterCode }}</pre>
        </div>

        <div v-if="section.archCode" class="mt-4">
          <pre class="code-block">{{ section.archCode }}</pre>
        </div>

        <div v-if="section.formula" class="mt-10">
          <pre class="code-block">{{ section.formula }}</pre>
        </div>

        <div v-if="section.actionCode" class="mt-10">
          <pre class="code-block">{{ section.actionCode }}</pre>
        </div>

        <div v-if="section.rounds" class="mt-10 space-y-4">
          <div
            v-for="round in section.rounds"
            :key="round.number"
            class="border border-border bg-bg-secondary p-5 md:p-6"
          >
            <div class="flex flex-wrap items-baseline gap-3">
              <span class="mono-label text-accent">{{ round.number }}</span>
              <h3 class="text-lg font-medium text-text-primary">{{ round.name }}</h3>
              <span class="text-sm text-text-tertiary">{{ round.dates }} · {{ round.format }}</span>
            </div>
            <div class="mt-4 grid gap-4 text-sm leading-relaxed text-text-secondary md:grid-cols-2 md:text-base">
              <div>
                <span class="mono-label text-text-tertiary">{{ t('schedule.challengeLabel') }}</span>
                <p class="mt-1">{{ round.challenge }}</p>
              </div>
              <div>
                <span class="mono-label text-text-tertiary">{{ t('schedule.participantsLabel') }}</span>
                <p class="mt-1">{{ round.participants }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div class="reveal mt-16 border-t border-border pt-12 text-center">
        <p class="text-lg text-text-secondary md:text-xl">
          {{ pick('Ready to build the next observer?', '准备好构建下一代观测员了吗？') }}
        </p>
        <router-link
          to="/register"
          class="mt-6 inline-block border border-accent px-6 py-3 font-mono text-[10px] uppercase tracking-[.12em] text-accent transition-colors hover:bg-accent hover:text-btn-text"
        >
          {{ t('nav.applyNow') }}
        </router-link>
      </div>
    </article>
  </main>
</template>
