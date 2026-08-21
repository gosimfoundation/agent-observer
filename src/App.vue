<script setup lang="ts">
import { provideI18n } from './composables/useI18n'
import { provideTheme } from './composables/useTheme'
import AppHeader from './components/layout/AppHeader.vue'
import AppFooter from './components/layout/AppFooter.vue'
import UnderConstructionModal from './components/effects/UnderConstructionModal.vue'

provideI18n()
provideTheme()
</script>

<template>
  <AppHeader />
  <router-view />
  <AppFooter />
  <UnderConstructionModal />
</template>
