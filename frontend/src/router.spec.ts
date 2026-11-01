import { expect, it, vi } from 'vitest'
vi.mock('./stores/session', () => ({ session: { restore: vi.fn().mockResolvedValue(false) }, client: {} }))
import { sessionGuard } from './router'
// Approved RUTA area, A1/A6 updated route table. Original numeric mapping unavailable.
it('RUTA-rule public song sections remain reachable without a session', async () => {
  for (const suffix of ['', '/acordes', '/tablatura', '/demos', '/escenario', '/compartir']) {
    const path = `/c/public-slug${suffix}`
    expect(await sessionGuard({ path, fullPath: path })).toBe(true)
  }
})
it('RUTA-rule private application routes keep their login redirect', async () => {
  expect(await sessionGuard({ path: '/canciones', fullPath: '/canciones' })).toEqual({ path: '/login', query: { redirect: '/canciones' } })
})
it('LAPP-011 opens the legal page without a session', async () => {
  expect(await sessionGuard({ path: '/legal', fullPath: '/legal#privacidad' })).toBe(true)
})
it('LAPP-013 keeps the login redirect on protected routes', async () => {
  for (const path of ['/canciones', '/perfil', '/bandas/nueva']) {
    expect(await sessionGuard({ path, fullPath: path })).toEqual({ path: '/login', query: { redirect: path } })
  }
})
it('HVW-003 sends a visitor without a session from the history to the login', async () => {
  const path = '/canciones/s1/historial'
  expect(await sessionGuard({ path, fullPath: path })).toEqual({ path: '/login', query: { redirect: path } })
})
