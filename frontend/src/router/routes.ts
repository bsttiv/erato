import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/features/compositions/DashboardView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bands',
    name: 'bands',
    component: () => import('@/features/bands/BandView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/bands/:id',
    name: 'band-detail',
    component: () => import('@/features/bands/BandView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('@/features/auth/AuthView.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('@/features/auth/AuthView.vue'),
    meta: { public: true, guestOnly: true },
  },
  {
    path: '/compositions/new',
    name: 'composition-create',
    component: () => import('@/features/compositions/CompositionCreateView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/new',
    redirect: '/compositions/new',
  },
  {
    path: '/compositions/:id',
    name: 'composition-detail',
    component: () => import('@/features/compositions/CompositionDetailView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/c/:ref',
    name: 'composition-public',
    component: () => import('@/features/compositions/CompositionDetailView.vue'),
    meta: { public: true },
  },
  {
    path: '/invite/:token',
    name: 'invite-redeem',
    component: () => import('@/features/sharing/InviteAcceptView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    redirect: '/',
  },
]
