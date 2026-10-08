import { effectScope, readonly, ref, watch } from 'vue'
import { getEntitlements, type Entitlements } from '@/api/entitlements'
import { getAccessToken } from '@/api/client'

const entitlements = ref<Entitlements | null>(null)
const error = ref<unknown>(null)
let pending: Promise<void> | null = null
let generation = 0
let watching = false

function ensureWatching(): void {
  if (!watching) {
    watching = true
    effectScope(true).run(() => {
      watch(() => !!getAccessToken(), () => { void refreshEntitlements() }, { flush: 'sync' })
    })
  }
}

export function refreshEntitlements(): Promise<void> {
  ensureWatching()
  const current = ++generation
  entitlements.value = null
  error.value = null
  pending = null
  if (!getAccessToken()) return Promise.resolve()
  const request = getEntitlements().then(value => {
    if (current === generation) entitlements.value = value
  }).catch(reason => {
    if (current === generation) error.value = reason
  }).finally(() => {
    if (current === generation) pending = null
  })
  pending = request
  return request
}

export function useEntitlements() {
  ensureWatching()
  if (getAccessToken() && !entitlements.value && !pending && !error.value) void refreshEntitlements()
  return { entitlements: readonly(entitlements), error: readonly(error), refresh: refreshEntitlements }
}
