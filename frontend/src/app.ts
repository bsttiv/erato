import { createApp, type App as VueApp } from 'vue'
import { createRouter, createWebHistory, type Router, type RouteRecordRaw } from 'vue-router'
import App from './App.vue'
import { routes } from './router/routes'
import { scrollBehavior, setupNavigationGuard } from './router/navigation'
import { refreshEntitlements } from './features/plan/useEntitlements'

import { EXTENSION_ROUTE_PREFIX, PAYMENT_EXTENSION_KEY, type PaymentExtension, type EratoAppOptions } from './extension'
export { EXTENSION_ROUTE_PREFIX, PAYMENT_EXTENSION_KEY, type PaymentNavItem, type PaymentExtension, type EratoAppOptions } from './extension'

export function createEratoRouter(payments?: PaymentExtension): Router {
  const extensionRecords: { path: string; name: RouteRecordRaw['name'] }[] = []
  function validate(records: RouteRecordRaw[], parent = ''): void {
    for (const route of records) {
      const path = route.path.startsWith('/') ? route.path : `${parent}/${route.path}`
      if (!path.startsWith(EXTENSION_ROUTE_PREFIX)) throw new Error('Payment routes must start with /plan')
      if (route.meta?.requiresAuth !== true || route.meta.public || route.meta.guestOnly) {
        throw new Error('Payment routes must require authentication')
      }
      extensionRecords.push({ path, name: route.name })
      if (route.children) validate(route.children, path)
    }
  }
  const extensionRoutes = payments?.routes ?? []
  validate(extensionRoutes)
  const catchAll = routes.findIndex(route => route.path.includes('pathMatch'))
  const router = createRouter({
    history: createWebHistory(),
    routes: [...routes.slice(0, catchAll), ...extensionRoutes, ...routes.slice(catchAll)],
    scrollBehavior,
  })
  if (payments?.bandCreationEntry) {
    try {
      const matched = router.resolve(payments.bandCreationEntry).matched
      if (!matched.some(record => extensionRecords.some(extension =>
        extension.name !== undefined ? record.name === extension.name : record.path === extension.path
      ))) throw new Error('Unregistered payment entry')
    } catch {
      throw new Error('Band creation entry must resolve to a registered payment route')
    }
  }
  setupNavigationGuard(router)
  router.afterEach((to, from, failure) => {
    if (!failure && from.path.startsWith(EXTENSION_ROUTE_PREFIX) && !to.path.startsWith(EXTENSION_ROUTE_PREFIX)) {
      void refreshEntitlements()
    }
  })
  return router
}

export function createEratoApp(options: EratoAppOptions = {}): VueApp {
  const router = createEratoRouter(options.payments)
  return createApp(App).provide(PAYMENT_EXTENSION_KEY, options.payments).use(router)
}
