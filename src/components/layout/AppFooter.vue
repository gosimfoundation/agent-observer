<script setup lang="ts">
import { useI18n } from '../../composables/useI18n'
const { t, pick } = useI18n()
</script>

<template>
  <footer class="border-t border-white/15 bg-[#0b0d12] py-10 text-white">
    <div class="mx-auto max-w-[1440px] px-6 md:px-10 xl:px-14">
      <div class="flex flex-col justify-between gap-8 md:flex-row md:items-end">
        <div>
          <div class="text-2xl font-semibold tracking-[-.05em]">GOSIM <span class="text-accent">/</span> {{ pick('AGENTIC COSMOS', '智能宇宙') }}</div>
          <div class="mt-3 max-w-xl text-xs text-white/45">{{ t('footer.copyright') }}</div>
        </div>
        <a href="https://gosim.org" target="_blank" rel="noopener" class="font-mono text-xs uppercase tracking-[.12em] text-white/60 transition-colors hover:text-white">
          {{ t('footer.mainSite') }} ↗
        </a>
      </div>
    </div>
  </footer>
</template>
