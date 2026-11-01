import { computed } from 'vue'
import { useRoute } from 'vue-router'

export function useCompositionPath() {
  const route = useRoute()
  // Authenticated screens load by song id; the public link keeps the slug.
  return computed(() => route.params.id
    ? `/canciones/${encodeURIComponent(route.params.id as string)}`
    : `/c/${encodeURIComponent(route.params.slug as string)}`)
}
export function sampleSlug(title: string): string {
  return title.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')
}
