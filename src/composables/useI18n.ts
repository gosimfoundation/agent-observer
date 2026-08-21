import { ref, provide, inject, watch, type InjectionKey, type Ref } from 'vue'
import en from '../i18n/en'
import zh from '../i18n/zh'

type Messages = Record<string, any>
type Locale = 'en' | 'zh'

const I18N_KEY: InjectionKey<{
  locale: Ref<Locale>
  t: (key: string) => any
  pick: <T>(english: T, chinese: T) => T
  toggleLocale: () => void
}> = Symbol('i18n')

const messages: Record<Locale, Messages> = { en, zh }

function getNestedValue(obj: any, path: string): any {
  return path.split('.').reduce((o, k) => o?.[k], obj) ?? path
}

export function provideI18n() {
  const savedLocale = typeof window !== 'undefined' ? window.localStorage.getItem('cosmos-locale') : null
  const locale = ref<Locale>(savedLocale === 'en' || savedLocale === 'zh' ? savedLocale : 'zh')

  if (typeof document !== 'undefined') {
    watch(locale, (value) => {
      document.documentElement.lang = value === 'zh' ? 'zh-CN' : 'en'
      document.title = value === 'zh'
        ? '巡天开源智能体黑客松 · GOSIM Hackathon'
        : 'Open Survey Agent Hackathon · GOSIM'
      const description = document.querySelector<HTMLMetaElement>('meta[name="description"]')
      if (description) {
        description.content = value === 'zh'
          ? 'GOSIM 巡天开源智能体黑客松：构建一个观测智能体，读取夜空状态，像资深观测员那样推理，并在每 900 秒决定下一次观测。'
          : 'The GOSIM Open Survey Agent Hackathon: build an observing agent that reads the night sky, reasons like a seasoned observer, and decides the next observation every 900 seconds.'
      }
      window.localStorage.setItem('cosmos-locale', value)
    }, { immediate: true })
  }

  function t(key: string): any {
    return getNestedValue(messages[locale.value], key)
  }

  function pick<T>(english: T, chinese: T): T {
    return locale.value === 'zh' ? chinese : english
  }



  function toggleLocale() {
    locale.value = locale.value === 'en' ? 'zh' : 'en'
  }

  provide(I18N_KEY, { locale, t, pick, toggleLocale })
  return { locale, t, pick, toggleLocale }
}

export function useI18n() {
  const i18n = inject(I18N_KEY)
  if (!i18n) throw new Error('useI18n() called without provideI18n()')
  return i18n
}
