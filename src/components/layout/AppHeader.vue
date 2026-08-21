<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from '../../composables/useI18n'
import { useTheme } from '../../composables/useTheme'

const { t, pick, toggleLocale } = useI18n()
const { isDark, toggleTheme } = useTheme()
const mobileOpen = ref(false)

type NavItem = { key: string; to?: string; href?: string }

const items: NavItem[] = [
  { key: 'nav.vision', to: '/vision' },
  { key: 'nav.about', href: '#about' },
  { key: 'nav.mission', href: '#mission' },
  { key: 'nav.participate', href: '#participate' },
  { key: 'nav.leaderboard', href: '#leaderboard' },
]

function scrollTo(hash: string) {
  mobileOpen.value = false
  document.querySelector(hash)?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <header class="sticky top-0 z-50 border-b border-border bg-bg-primary/92 backdrop-blur">
    <div class="mx-auto flex h-16 max-w-[1440px] items-center justify-between gap-6 px-6 md:px-10 xl:px-14">
      <a href="#" @click.prevent="scrollTo('#top')" class="flex items-center gap-3">
        <span class="text-lg font-semibold tracking-[-.05em] text-text-primary">GOSIM</span>
        <span class="hidden h-4 w-px bg-border sm:block"></span>
        <span class="hidden max-w-[22ch] font-mono text-[10px] uppercase leading-tight tracking-[.1em] text-text-tertiary sm:block">
          {{ pick('Open Survey Agent Hackathon', '巡天开源智能体黑客松') }}
        </span>
      </a>

      <nav class="hidden items-center gap-5 lg:flex">
        <router-link
          v-for="item in items.filter(i => i.to)"
          :key="item.to"
          :to="item.to!"
          class="font-mono text-[10px] uppercase tracking-[.08em] text-text-tertiary transition-colors hover:text-accent"
        >{{ t(item.key) }}</router-link>
        <a
          v-for="item in items.filter(i => i.href)"
          :key="item.href"
          :href="item.href"
          @click.prevent="scrollTo(item.href!)"
          class="font-mono text-[10px] uppercase tracking-[.08em] text-text-tertiary transition-colors hover:text-accent"
        >{{ t(item.key) }}</a>
      </nav>

      <div class="flex items-center gap-2">
        <button
          @click="toggleTheme"
          class="border border-border p-1 text-text-tertiary transition-colors hover:text-text-primary"
          :title="isDark ? pick('Switch to light mode', '切换为浅色模式') : pick('Switch to dark mode', '切换为深色模式')"
        >
          <svg v-if="isDark" class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><path d="M12 1v2m0 18v2M4.22 4.22l1.42 1.42m12.72 12.72 1.42 1.42M1 12h2m18 0h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"/></svg>
          <svg v-else class="h-4 w-4" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
        </button>
        <button @click="toggleLocale" class="border border-border px-2 py-1 font-mono text-[10px] uppercase tracking-[.08em] text-text-tertiary transition-colors hover:text-text-primary">
          {{ pick('中文', 'EN') }}
        </button>
        <router-link to="/register" class="ml-1 hidden border border-accent px-3 py-2 font-mono text-[10px] uppercase tracking-[.1em] text-accent md:inline">{{ t('nav.applyNow') }}</router-link>
        <button class="ml-1 lg:hidden" @click="mobileOpen = !mobileOpen" :aria-label="pick('Menu', '菜单')">
          <svg class="h-6 w-6 text-text-primary" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
        </button>
      </div>
    </div>

    <div v-if="mobileOpen" class="border-t border-border bg-bg-primary px-6 py-4 lg:hidden">
      <router-link
        v-for="item in items.filter(i => i.to)"
        :key="item.to"
        :to="item.to!"
        @click="mobileOpen = false"
        class="block py-3 text-text-tertiary transition-colors hover:text-text-primary"
      >{{ t(item.key) }}</router-link>
      <a
        v-for="item in items.filter(i => i.href)"
        :key="item.href"
        :href="item.href"
        @click.prevent="scrollTo(item.href!)"
        class="block py-3 text-text-tertiary transition-colors hover:text-text-primary"
      >{{ t(item.key) }}</a>
    </div>
  </header>
</template>
