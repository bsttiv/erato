import { createRouter, createWebHistory } from 'vue-router'
import LandingView from './views/LandingView.vue'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import CompositionsView from './views/CompositionsView.vue'
import NewCompositionView from './views/NewCompositionView.vue'
import CreateBandView from './views/CreateBandView.vue'
import CompositionView from './views/CompositionView.vue'
import ChordEditorView from './views/ChordEditorView.vue'
import TabEditorView from './views/TabEditorView.vue'
import DemosView from './views/DemosView.vue'
import StageView from './views/StageView.vue'
import ShareView from './views/ShareView.vue'
import ProfileView from './views/ProfileView.vue'

export const routes = [
  { path: '/', component: LandingView },
  { path: '/login', component: LoginView },
  { path: '/registro', component: RegisterView },
  { path: '/composiciones', component: CompositionsView },
  { path: '/composiciones/nueva', component: NewCompositionView },
  { path: '/bandas/nueva', component: CreateBandView },
  { path: '/c/noche-de-otono', component: CompositionView },
  { path: '/c/noche-de-otono/acordes', component: ChordEditorView },
  { path: '/c/noche-de-otono/tablatura', component: TabEditorView },
  { path: '/c/noche-de-otono/demos', component: DemosView },
  { path: '/c/noche-de-otono/escenario', component: StageView },
  { path: '/c/noche-de-otono/compartir', component: ShareView },
  { path: '/perfil', component: ProfileView },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to) {
    if (to.hash) return { el: to.hash, behavior: 'smooth' }
    return { top: 0 }
  },
})
