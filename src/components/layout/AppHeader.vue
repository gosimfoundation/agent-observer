<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from '../../composables/useI18n'

const { t, pick, toggleLocale } = useI18n()
const router = useRouter()
const mobileOpen = ref(false)

type NavItem = { key: string; to?: string; href?: string }

const items: NavItem[] = [
  { key: 'nav.vision', to: '/brief' },
  { key: 'nav.about', href: '#about' },
  { key: 'nav.mission', href: '#mission' },
  { key: 'nav.participate', href: '#participate' },
  { key: 'nav.leaderboard', href: '#leaderboard' },
]

function scrollTo(hash: string) {
  mobileOpen.value = false
  if (router.currentRoute.value.path !== '/') {
    router.push({ path: '/', hash })
    return
  }
  document.querySelector(hash)?.scrollIntoView({ behavior: 'smooth' })
}
</script>

<template>
  <header class="cosmos-header sticky top-0 z-50 border-b border-border backdrop-blur">
    <div class="mx-auto flex h-16 max-w-[1600px] items-center justify-between gap-6 px-5 md:px-10 xl:px-14">
      <router-link to="/" class="flex items-baseline gap-3">
        <span class="cosmos-wordmark text-lg text-[#f5f5f5]">OPEN <span class="text-[#315efb]">SURVEY</span></span>
        <span class="hidden h-4 w-px bg-white/25 sm:block"></span>
        <span class="hidden max-w-[22ch] font-mono text-xs uppercase leading-[1.35] tracking-[.1em] text-white/45 sm:block">
          AGENT HACKATHON // 2026
        </span>
      </router-link>

      <nav class="hidden items-center gap-5 lg:flex">
        <router-link
          v-for="item in items.filter(i => i.to)"
          :key="item.to"
          :to="item.to!"
          class="inline-flex h-10 items-center font-mono text-xs uppercase tracking-[.06em] text-white/50 transition-colors hover:text-[#315efb]"
        >{{ t(item.key) }}</router-link>
        <a
          v-for="item in items.filter(i => i.href)"
          :key="item.href"
          :href="item.href"
          @click.prevent="scrollTo(item.href!)"
          class="inline-flex h-10 items-center font-mono text-xs uppercase tracking-[.06em] text-white/50 transition-colors hover:text-[#315efb]"
        >{{ t(item.key) }}</a>
      </nav>

      <div class="flex items-center gap-2">
        <button @click="toggleLocale" class="inline-flex h-10 min-w-12 items-center justify-center border border-white/25 px-2 font-mono text-xs uppercase text-white/55 transition-colors hover:border-white/60 hover:text-white">
          {{ pick('中文', 'EN') }}
        </button>
        <span aria-disabled="true" class="cosmos-register-link pointer-events-none ml-1 hidden h-10 items-center border px-4 font-mono text-xs font-semibold uppercase tracking-widest md:inline-flex">{{ pick('Registration coming soon', '报名即将开始') }}</span>
        <button class="ml-1 lg:hidden" @click="mobileOpen = !mobileOpen" :aria-label="pick('Menu', '菜单')">
          <svg class="h-6 w-6 text-text-primary" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
        </button>
      </div>
    </div>

    <div v-if="mobileOpen" class="border-t border-white/20 bg-[#070708] px-5 py-4 lg:hidden">
      <router-link
        v-for="item in items.filter(i => i.to)"
        :key="item.to"
        :to="item.to!"
        @click="mobileOpen = false"
        class="block border-b border-white/10 py-3 text-base text-white/60 transition-colors hover:text-white"
      >{{ t(item.key) }}</router-link>
      <a
        v-for="item in items.filter(i => i.href)"
        :key="item.href"
        :href="item.href"
        @click.prevent="scrollTo(item.href!)"
        class="block border-b border-white/10 py-3 text-base text-white/60 transition-colors hover:text-white"
      >{{ t(item.key) }}</a>
      <span aria-disabled="true" class="cosmos-register-link pointer-events-none mt-3 block border px-4 py-3 text-center font-mono text-xs font-semibold uppercase tracking-widest">
        {{ pick('Registration coming soon', '报名即将开始') }}
      </span>
    </div>
  </header>
</template>
