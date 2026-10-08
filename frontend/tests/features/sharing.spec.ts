import { it, expect, vi } from 'vitest'
import { ref } from 'vue'
import { mount, flushPromises } from '@vue/test-utils'
import SharingModal from '@/features/sharing/SharingModal.vue'
import * as sharing from '@/api/sharing'
vi.mock('@/features/plan/useEntitlements', () => ({ useEntitlements: () => ({ entitlements: ref(null) }) }))
it('preserves boolean visibility event compatibility and hides management for non-owners', async () => {
  vi.spyOn(sharing, 'setVisibility').mockResolvedValue({ visibility: 'public' } as any)
  const w = mount(SharingModal, { props: { compositionId: 'c', isPublic: false, canManage: false } })
  await w.findAll('.er-share-card')[0].trigger('click'); await flushPromises()
  expect(w.emitted('visibilityChanged')?.[0]).toEqual([true])
  expect(w.find('select').exists()).toBe(false)
})
