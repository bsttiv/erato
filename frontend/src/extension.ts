import type { InjectionKey } from 'vue'
import type { RouteRecordRaw, RouteLocationRaw } from 'vue-router'

export const EXTENSION_ROUTE_PREFIX = '/plan'
export interface PaymentNavItem { label: string; to: RouteLocationRaw }
export interface PaymentExtension {
  routes: RouteRecordRaw[]
  navItems?: PaymentNavItem[]
  bandCreationEntry?: RouteLocationRaw
}
export interface EratoAppOptions { payments?: PaymentExtension }
export const PAYMENT_EXTENSION_KEY: InjectionKey<PaymentExtension | undefined> = Symbol('payments')

