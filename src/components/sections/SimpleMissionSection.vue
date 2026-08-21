<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'

const { t } = useI18n()

type Card = { title: string; desc: string }
const cards = computed(() => t('home.mission.cards') as Card[])
</script>

<template>
  <section id="mission" class="bg-bg-secondary py-24 md:py-36">
    <div class="mx-auto max-w-[1440px] px-6 md:px-10 xl:px-14">
      <div class="reveal max-w-3xl">
        <span class="section-kicker">{{ t('home.mission.kicker') }}</span>
        <h2 class="section-title mt-8">{{ t('home.mission.title') }}</h2>
        <p class="mt-6 text-lg leading-relaxed text-text-secondary md:text-xl">{{ t('home.mission.lede') }}</p>
      </div>

      <div class="mt-16 grid gap-px overflow-hidden border border-border bg-border md:grid-cols-3">
        <div
          v-for="(card, index) in cards"
          :key="index"
          class="reveal bg-bg-primary p-8 md:p-10"
          :class="`reveal-delay-${index + 1}`"
        >
          <span class="mono-label text-accent">0{{ index + 1 }}</span>
          <h3 class="mt-5 text-xl font-medium text-text-primary">{{ card.title }}</h3>
          <p class="mt-3 text-sm leading-relaxed text-text-secondary md:text-base">{{ card.desc }}</p>
        </div>
      </div>

      <p class="reveal reveal-delay-4 mt-12 max-w-3xl text-base leading-relaxed text-text-secondary md:text-lg">
        {{ t('home.mission.closing') }}
      </p>
    </div>
  </section>
</template>
