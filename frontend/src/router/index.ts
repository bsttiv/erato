import {
  createRouter,
  createWebHistory,
  type Router,
  type RouterScrollBehavior,
} from 'vue-router'
import { routes } from './routes'
import { ensureAuthReady, isAuthenticated } from './authReady'

export { routes } from './routes'

export const scrollBehavior: RouterScrollBehavior = (to, _from, savedPosition) => {
  if (savedPosition) {
    return savedPosition
  }
  if (to.hash) {
    return {
      el: to.hash,
      behavior: 'smooth',
    }
  }
  return { top: 0 }
}

export function setupNavigationGuard(router: Router): void {
  router.beforeEach(async (to) => {
    await ensureAuthReady()
    const isAuth = isAuthenticated()

    if (to.meta.guestOnly && isAuth) {
      return '/'
    }

    if (to.meta.public) {
      return true
    }

    if (isAuth) {
      return true
    }

    return {
      path: '/login',
      query: { next: to.fullPath },
    }
  })
}

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior,
})

setupNavigationGuard(router)

export default router
