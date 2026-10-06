export function getAppUrl(): string {
  const envUrl = (import.meta.env?.VITE_APP_URL as string | undefined) ?? ''
  const trimmed = envUrl.trim().replace(/\/+$/, '')
  return trimmed || 'http://localhost:5173'
}

export function getLoginUrl(): string {
  return `${getAppUrl()}/login`
}

export function getRegisterUrl(): string {
  return `${getAppUrl()}/register`
}
