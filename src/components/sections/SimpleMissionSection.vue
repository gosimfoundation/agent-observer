<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'
import MissionPanel from '../MissionPanel.vue'
import observedUniverseImage from '../../assets/images/survey-observed-universe.jpg'

const { t, pick } = useI18n()
type Card = { title: string; desc: string }
const cards = computed(() => t('home.mission.cards') as Card[])
</script>

<template>
  <section id="mission" class="poster-section poster-canvas py-24 md:py-40">
    <div class="mission-aura plasma-field" aria-hidden="true"></div>
    <div class="mx-auto max-w-[1600px] px-5 md:px-10 xl:px-14">
      <div class="grid gap-14 lg:grid-cols-[.85fr_1.15fr] lg:gap-24">
        <div class="reveal relative z-10 lg:sticky lg:top-28 lg:self-start">
          <div class="flex items-start justify-between">
            <span class="poster-kicker">{{ t('home.mission.kicker') }}</span>
            <span class="font-mono text-xs uppercase tracking-[.1em] text-[#edb28b]">02 / 04</span>
          </div>
          <h2 class="section-title distressed-type mt-10">{{ t('home.mission.title') }}</h2>
          <p class="mt-7 max-w-xl text-base leading-relaxed text-text-secondary md:text-lg">{{ t('home.mission.lede') }}</p>

        </div>

        <div class="relative z-10">
          <!-- One decision in three beats: the same patch of sky, known better
               and with fewer options open, each step down the page. -->
          <article
            v-for="(card, index) in cards" :key="card.title"
            class="poster-card reveal py-9 md:grid md:grid-cols-[5rem_1fr_17rem] md:items-start md:gap-8 md:py-12"
            :class="`reveal-delay-${index + 1}`"
          >
            <span class="font-mono text-xs text-[#edb28b]">0{{ index + 1 }}</span>
            <div class="mt-5 md:mt-0">
              <h3 class="max-w-[18ch] text-xl font-semibold leading-tight tracking-[-.03em] text-[#f0e9dd] md:text-2xl">{{ card.title }}</h3>
              <p class="mt-4 max-w-xl text-sm leading-relaxed text-text-secondary">{{ card.desc }}</p>
            </div>
            <MissionPanel class="mt-7 md:mt-0" :panel="(index + 1) as 1 | 2 | 3" />
          </article>

          <figure class="survey-figure survey-figure--plate reveal mt-12">
            <div class="survey-plate paper-sheet">
              <img :src="observedUniverseImage" :alt="pick('Mock universe observed by a balanced agent observer', '均衡型观测智能体观测到的模拟宇宙')" loading="lazy">
            </div>
            <figcaption>
              {{ pick('What a run actually produces: the mock galaxies and quasars your agent chose to observe. Different policies leave different cosmic structure visible.', '一次运行的真实产出：你的智能体选择观测到的模拟星系与类星体。不同的策略，会留下不同的宇宙结构。') }}
            </figcaption>
          </figure>

          <div class="reveal mt-12 paper-sheet p-7 md:p-10">
            <span class="font-mono text-xs uppercase tracking-[.1em] text-[#edb28b]">{{ pick('Entry requirement', '参赛要求') }}</span>
            <p class="relative z-10 mt-5 max-w-[22ch] text-xl font-semibold leading-relaxed tracking-[-.02em] md:text-3xl">{{ t('home.mission.closing') }}</p>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.mission-aura { top: 35%; left: -26rem; width: 55rem; opacity: .38; transform: rotate(72deg); }
</style>
