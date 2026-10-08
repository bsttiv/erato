import '@design-system/tokens.css'
import '@design-system/components/bundle.css'
import './styles/layout.css'
import { createEratoApp } from './app'
import { ensureAuthReady } from './router/authReady'

ensureAuthReady()
createEratoApp().mount('#app')
