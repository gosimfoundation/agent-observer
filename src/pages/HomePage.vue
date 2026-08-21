<script setup lang="ts">
import { useScrollReveal } from '../composables/useScrollReveal'
import HeroSection from '../components/sections/HeroSection.vue'
import SimpleVisionSection from '../components/sections/SimpleVisionSection.vue'
import SimpleMissionSection from '../components/sections/SimpleMissionSection.vue'
import SimpleParticipateSection from '../components/sections/SimpleParticipateSection.vue'
import LeaderboardSection from '../components/sections/LeaderboardSection.vue'
import CtaSection from '../components/sections/CtaSection.vue'

useScrollReveal()
</script>

<template>
  <main>
    <HeroSection />
    <SimpleVisionSection />
    <SimpleMissionSection />
    <SimpleParticipateSection />
    <LeaderboardSection />
    <CtaSection />
  </main>
</template>
