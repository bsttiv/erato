export function getAppUrl(): string {
  const envUrl = import.meta.env?.VITE_APP_URL || (typeof process !== 'undefined' ? process.env?.VITE_APP_URL : '') || ''
  return envUrl.replace(/\/+$/, '')
}

export function getLoginUrl(): string {
  const base = getAppUrl()
  return base ? `${base}/login` : '/login'
}

export function getRegisterUrl(): string {
  const base = getAppUrl()
  return base ? `${base}/register` : '/register'
}
