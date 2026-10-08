import { createEratoRouter } from '@/app'

export { routes } from './routes'
export { scrollBehavior, setupNavigationGuard } from './navigation'

export const router = createEratoRouter()
export default router
