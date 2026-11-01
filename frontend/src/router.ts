import { createRouter, createWebHistory } from 'vue-router'
import LandingView from './pages/LandingView.vue'
import LegalView from './pages/LegalView.vue'
import HistoryView from './pages/HistoryView.vue'
import LoginView from './pages/LoginView.vue'
import RegisterView from './pages/RegisterView.vue'
import CompositionsView from './pages/CompositionsView.vue'
import NewCompositionView from './pages/NewCompositionView.vue'
import CreateBandView from './pages/CreateBandView.vue'
import BandView from './pages/BandView.vue'
import CompositionView from './pages/CompositionView.vue'
import ChordEditorView from './pages/ChordEditorView.vue'
import TabEditorView from './pages/TabEditorView.vue'
import DemosView from './pages/DemosView.vue'
import StageView from './pages/StageView.vue'
import ShareView from './pages/ShareView.vue'
import { session } from './stores/session'
import InvitationView from './pages/InvitationView.vue'
import ProfileView from './pages/ProfileView.vue'

export const routes = [
  { path: '/', component: LandingView },
  { path: '/legal', component: LegalView },
  { path: '/login', component: LoginView },
  { path: '/registro', component: RegisterView },
  { path: '/canciones', component: CompositionsView },
  { path: '/canciones/nueva', component: NewCompositionView },
  { path: '/bandas/nueva', component: CreateBandView },
  { path: '/bandas/:id', component: BandView },
  { path: '/canciones/:id', component: CompositionView },
  { path: '/canciones/:id/acordes', component: ChordEditorView },
  { path: '/canciones/:id/tablatura', component: TabEditorView },
  { path: '/canciones/:id/demos', component: DemosView },
  { path: '/canciones/:id/historial', component: HistoryView },
  { path: '/canciones/:id/escenario', component: StageView },
  { path: '/canciones/:id/compartir', component: ShareView },
  // Public share link: read-only screens addressed by slug, no sign-in needed.
  { path: '/c/:slug', component: CompositionView },
  { path: '/c/:slug/acordes', component: ChordEditorView },
  { path: '/c/:slug/tablatura', component: TabEditorView },
  { path: '/c/:slug/demos', component: DemosView },
  { path: '/c/:slug/escenario', component: StageView },
  { path: '/i/:token', component: InvitationView },
  { path: '/perfil', component: ProfileView },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})

export async function sessionGuard({ path, fullPath }: { path: string; fullPath: string }) {
  const publicRoute = ['/', '/login', '/registro', '/legal'].includes(path) || /^\/c\/[^/]+(?:\/[^/]+)?\/?$/.test(path) || path.startsWith('/i/')
  if (publicRoute) return true
  try {
    if (await session.restore()) return true
  } catch (error) {
    // A temporary upstream or network failure sends the visitor to login; the httpOnly refresh cookie stays, so a later attempt can still restore the session.
  }
  return { path: '/login', query: { redirect: fullPath } }
}
router.beforeEach(sessionGuard)
export default router
