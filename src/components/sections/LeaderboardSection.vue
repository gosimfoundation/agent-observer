<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from '../../composables/useI18n'
import { useLeaderboard } from '../../composables/useLeaderboard'
const { t, pick } = useI18n()
const { entries, loading, refreshing, error, updatedAt, reload, leaderboardUrl } = useLeaderboard(20)
const updated = computed(() => updatedAt.value?.toLocaleTimeString(pick('en-US', 'zh-CN')) || '')
const metric = (value: number | null) => value == null ? '—' : value.toFixed(2)
</script>
<template>
  <section id="leaderboard" class="bg-bg-primary py-24 md:py-36"><div class="mx-auto max-w-[1440px] px-6 md:px-10 xl:px-14">
    <div class="grid gap-10 lg:grid-cols-[.7fr_1.3fr] lg:gap-20"><div class="reveal"><span class="section-kicker">{{ t('home.leaderboard.kicker') }}</span><h2 class="section-title mt-8">{{ t('home.leaderboard.title') }}</h2><p class="mt-8 max-w-lg leading-relaxed text-text-secondary">{{ t('home.leaderboard.lede') }}</p></div>
    <div class="reveal reveal-delay-1"><div class="flex items-center justify-between border-b border-border pb-4"><span v-if="updated" class="mono-label text-text-muted">{{ t('leaderboard.updated') }} {{ updated }}</span><div class="ml-auto flex gap-4"><button class="mono-label text-text-muted hover:text-accent disabled:opacity-50" :disabled="refreshing" @click="reload">↻ {{ t('leaderboard.refresh') }}</button><a v-if="leaderboardUrl !== '#'" :href="leaderboardUrl" target="_blank" rel="noopener" class="mono-label text-accent">{{ t('leaderboard.full') }} ↗</a></div></div>
      <p v-if="loading" class="mt-6 text-sm text-text-secondary">{{ t('leaderboard.loading') }}</p><p v-else-if="error && !entries.length" class="mt-6 text-sm text-text-secondary">{{ t('leaderboard.unavailable') }}</p><p v-else-if="!entries.length" class="mt-6 text-sm text-text-secondary">{{ t('leaderboard.empty') }}</p>
      <div v-else class="overflow-x-auto"><table class="w-full min-w-[720px] border-collapse text-left"><thead><tr class="border-b border-border"><th class="mono-label py-3">#</th><th class="mono-label py-3">{{ t('leaderboard.team') }}</th><th class="mono-label py-3 text-right">{{ t('leaderboard.score') }}</th><th class="mono-label py-3 text-right">{{ t('leaderboard.science') }}</th><th class="mono-label py-3 text-right">{{ t('leaderboard.completion') }}</th><th class="mono-label py-3 text-right">{{ t('leaderboard.uniformity') }}</th><th class="mono-label py-3 text-right">{{ t('leaderboard.submissions') }}</th></tr></thead><tbody><tr v-for="row in entries" :key="`${row.rank}:${row.name}`" class="border-b border-border-subtle"><td class="py-3 font-mono text-xs text-accent">{{ row.rank }}</td><td class="py-3 text-sm font-medium text-text-primary">{{ row.name }}</td><td class="py-3 text-right font-mono text-sm">{{ metric(row.score) }}</td><td class="py-3 text-right font-mono text-sm">{{ metric(row.science) }}</td><td class="py-3 text-right font-mono text-sm">{{ metric(row.completion) }}</td><td class="py-3 text-right font-mono text-sm">{{ metric(row.uniformity) }}</td><td class="py-3 text-right font-mono text-sm">{{ row.submissions }}</td></tr></tbody></table></div>
    </div></div>
  </div></section>
</template>
