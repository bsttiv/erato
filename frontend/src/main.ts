import '@design-system/tokens.css'
import '@design-system/components/bundle.css'
import './styles/layout.css'
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { ensureAuthReady } from './router/authReady'

// Start bootstrap refresh immediately
ensureAuthReady()

const app = createApp(App)
app.use(router)
app.mount('#app')
