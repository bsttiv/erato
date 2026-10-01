import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DemoUploadModal from '@/features/demos/DemoUploadModal.vue'
import * as demosApi from '@/api/demos'

describe('Demos upload flow (direct-to-Cloudinary)', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('never sends file bytes through backend API and uploads directly to Cloudinary', async () => {
    // Step A mock: backend signature endpoint
    const signatureSpy = vi.spyOn(demosApi, 'requestUploadSignature').mockResolvedValueOnce({
      signature: 'test_sha_sig',
      timestamp: 1700000000,
      folder: 'erato/compositions/comp-1',
      api_key: 'cloud_api_key_123',
      cloud_name: 'erato_cloud',
      resource_type: 'video',
      type: 'authenticated',
      tags: 'pending',
    })

    // Step B/C mock: direct POST to Cloudinary
    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(
        JSON.stringify({
          public_id: 'erato/compositions/comp-1/take-1',
          version: 12345,
          signature: 'cloudinary_return_sig',
          resource_type: 'video',
          duration: 45.5,
          bytes: 1048576,
          format: 'mp3',
        }),
        { status: 200, headers: { 'Content-Type': 'application/json' } }
      )
    )

    // Step D mock: backend confirmation endpoint
    const confirmSpy = vi.spyOn(demosApi, 'confirmUpload').mockResolvedValueOnce({
      id: 'demo-1',
      title: 'Toma ensayo 1',
      public_id: 'erato/compositions/comp-1/take-1',
      duration: 45.5,
    })

    const wrapper = mount(DemoUploadModal, {
      props: {
        compositionId: 'comp-1',
      },
    })

    // Provide title and file
    const titleInput = wrapper.find('input[type="text"]')
    await titleInput.setValue('Toma ensayo 1')

    const file = new File(['fake-audio-bytes'], 'take1.mp3', { type: 'audio/mp3' })
    const fileInput = wrapper.find('input[type="file"]')
    Object.defineProperty(fileInput.element, 'files', {
      value: [file],
      writable: false,
    })
    await fileInput.trigger('change')

    // Submit upload form
    await wrapper.find('form').trigger('submit')
    await flushPromises()

    // 1. Verify backend signature call carries NO file body
    expect(signatureSpy).toHaveBeenCalledTimes(1)
    expect(signatureSpy).toHaveBeenCalledWith('comp-1')

    // 2. Verify direct Cloudinary upload target URL
    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [cloudinaryUrl, cloudinaryInit] = fetchSpy.mock.calls[0]
    expect(cloudinaryUrl.toString()).toContain('api.cloudinary.com/v1_1/erato_cloud/auto/upload')

    // 3. Verify formData passed to Cloudinary contains the file
    const formData = cloudinaryInit?.body as FormData
    expect(formData.get('file')).toBeDefined()
    expect(formData.get('api_key')).toBe('cloud_api_key_123')
    expect(formData.get('signature')).toBe('test_sha_sig')
    expect(formData.get('tags')).toBe('pending')
    expect(formData.get('tags')).not.toBe('undefined')

    // 4. Verify confirmation payload with references only (no audio binary)
    expect(confirmSpy).toHaveBeenCalledTimes(1)
    const [compArg, payloadArg] = confirmSpy.mock.calls[0]
    expect(compArg).toBe('comp-1')
    expect(payloadArg.public_id).toBe('erato/compositions/comp-1/take-1')
    expect(payloadArg.signature).toBe('cloudinary_return_sig')
    expect((payloadArg as any).file).toBeUndefined()
    expect((payloadArg as any).data).toBeUndefined()

    expect(wrapper.emitted('uploaded')).toBeTruthy()
  })
})
