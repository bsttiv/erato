import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { createEratoApp, createEratoRouter, PAYMENT_EXTENSION_KEY } from '@/app'
import AppNavExtras from '@/shared/AppNavExtras.vue'
import { setAccessToken } from '@/api/client'
import { resetAuthReadyForTesting, setAuthenticated } from '@/router/authReady'
import * as entitlements from '@/features/plan/useEntitlements'

const page = { template: '<p>Pago</p>' }
const payments = {
  routes: [{ path: '/plan', name: 'plan', component: page, meta: { requiresAuth: true } }],
  navItems: [{ label: 'Tu plan', to: { name: 'plan' } }],
  bandCreationEntry: { name: 'plan' },
}
afterEach(() => { setAccessToken(null); resetAuthReadyForTesting(); vi.restoreAllMocks() })
describe('Payment app factory', () => {
  it.each(['/planet', '/planilla'])('rejects payment-like top-level path %s', path => {
    expect(() => createEratoApp({ payments: { routes: [
      { path, component: page, meta: { requiresAuth: true } },
    ] } })).toThrow('Payment routes must start with /plan')
  })
  it.each(['/planet', '/planilla'])('rejects payment-like absolute child path %s', path => {
    expect(() => createEratoApp({ payments: { routes: [{
      path: '/plan', component: page, meta: { requiresAuth: true },
      children: [{ path, component: page, meta: { requiresAuth: true } }],
    }] } })).toThrow('Payment routes must start with /plan')
  })
  it.each(['/plan', '/plan/bands/new'])('accepts payment path %s', path => {
    const app = createEratoApp({ payments: { routes: [
      { path, component: page, meta: { requiresAuth: true } },
    ] } })
    const router = app.config.globalProperties.$router
    expect(router.resolve(path).matched.some(record => record.path === path)).toBe(true)
    router.options.history.destroy()
  })
  it.each([
    ['/planet', '/', 0], ['/planilla', '/', 0],
    ['/plan', '/planet', 1], ['/plan/bands/new', '/planilla', 1],
    ['/plan', '/plan/bands/new', 0],
  ] as const)('refreshes only on leaving payment paths: %s -> %s', async (from, to, calls) => {
    const refresh = vi.spyOn(entitlements, 'refreshEntitlements').mockResolvedValue(undefined)
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ access_token: 'jwt' })))
    setAccessToken('jwt')
    setAuthenticated(true)
    const router = createEratoRouter({ routes: [
      { path: '/plan', component: page, meta: { requiresAuth: true } },
      { path: '/plan/bands/new', component: page, meta: { requiresAuth: true } },
    ] })
    // Non-payment host routes let the refresh boundary be exercised independently of registration.
    for (const path of ['/planet', '/planilla']) router.addRoute({ path, component: page })
    await router.push(from)
    expect(router.currentRoute.value.path).toBe(from)
    refresh.mockClear()
    await router.push(to)
    expect(refresh).toHaveBeenCalledTimes(calls)
    router.options.history.destroy()
  })
  it('creates only one browser history for a registered entry', () => {
    const listen = vi.spyOn(window, 'addEventListener')
    const router = createEratoRouter(payments)
    expect(listen.mock.calls.filter(([event]) => event === 'popstate')).toHaveLength(1)
    router.options.history.destroy()
  })
  it.each(['/', '/missing-payment-entry'])('rejects a non-extension path entry %s', path => {
    expect(() => createEratoRouter({ ...payments, bandCreationEntry: { path } })).toThrow(
      'Band creation entry must resolve to a registered payment route'
    )
  })
  it('accepts an unnamed nested extension entry by path', () => {
    const router = createEratoRouter({ routes: [{
      path: '/plan', component: page, meta: { requiresAuth: true },
      children: [{ path: 'checkout', component: page, meta: { requiresAuth: true } }],
    }], bandCreationEntry: '/plan/checkout' })
    expect(router.resolve('/plan/checkout').matched).toHaveLength(2)
    router.options.history.destroy()
  })
  it('has no payment route or navigation without an extension', () => {
    expect(createEratoRouter().getRoutes().some(r => r.path.startsWith('/plan'))).toBe(false)
    expect(mount(AppNavExtras).findAll('a')).toHaveLength(0)
  })
  it.each([
    { ...payments, routes: [{ ...payments.routes[0], path: '/bands' }] },
    { ...payments, routes: [{ ...payments.routes[0], meta: {} }] },
    { ...payments, bandCreationEntry: { name: 'dashboard' } },
  ])('rejects invalid registration %#', extension => {
    expect(() => createEratoApp({ payments: extension })).toThrow()
  })
  it('inserts payment routes before catch-all and renders inside the shared shell', async () => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ access_token: 'jwt' })))
    const app = createEratoApp({ payments })
    const router = app.config.globalProperties.$router
    const records = router.options.routes
    expect(records.findIndex(r => r.path === '/plan')).toBeLessThan(records.findIndex(r => r.path.includes('pathMatch')))
    await router.push('/plan')
    const host = document.createElement('div')
    app.mount(host)
    await nextTick()
    expect(host.querySelector('.er-app')?.textContent).toContain('Pago')
    expect(router.currentRoute.value.name).toBe('plan')
    app.unmount()
  })
  it('renders working nav links only while authenticated', async () => {
    const router = createEratoRouter(payments)
    const wrapper = mount(AppNavExtras, { global: { plugins: [router], provide: { [PAYMENT_EXTENSION_KEY as symbol]: payments } } })
    expect(wrapper.findAll('a')).toHaveLength(0)
    setAccessToken('jwt')
    setAuthenticated(true)
    await nextTick()
    expect(wrapper.get('a').text()).toBe('Tu plan')
    expect(wrapper.get('a').attributes('href')).toBe('/plan')
    expect(wrapper.get('a').classes()).toContain('er-btn')
    setAccessToken(null)
    await nextTick()
    expect(wrapper.findAll('a')).toHaveLength(0)
    wrapper.unmount()
  })
})
