import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import DemoUploadModal from '@/features/demos/DemoUploadModal.vue'
import DemosSection from '@/features/demos/DemosSection.vue'
import * as demosApi from '@/api/demos'
import * as clientModule from '@/api/client'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

const backendDemo = {
  demo_id: 'd1',
  cloudinary_public_id: 'erato/compositions/c1/take',
  title: 'Toma 1',
  duration_s: 36.0065,
  uploaded_by: 'u1',
  uploaded_at: '2026-10-01T10:00:00Z',
}

const backendComment = {
  id: 'cm1',
  composition_id: 'c1',
  demo_id: 'd1',
  author_id: 'u1',
  author_name: 'Ana',
  timestamp_s: 12.5,
  text: 'Entra la guitarra',
  created_at: '2026-10-01T10:05:00Z',
}

describe('demos API client contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('confirmUpload sends the exact backend body and maps the response', async () => {
    const spy = vi
      .spyOn(clientModule, 'apiClient')
      .mockResolvedValueOnce(jsonResponse(backendDemo, 201))

    const take = await demosApi.confirmUpload('c1', {
      public_id: 'erato/compositions/c1/take',
      version: 1790876123,
      signature: 'sig',
      title: 'Toma 1',
      duration: 36.0065,
    })

    const [url, init] = spy.mock.calls[0]
    expect(url).toBe('/compositions/c1/demos')
    const body = JSON.parse(init!.body as string)
    expect(body).toEqual({
      public_id: 'erato/compositions/c1/take',
      version: '1790876123',
      signature: 'sig',
      title: 'Toma 1',
      duration_s: 36.0065,
    })
    expect(typeof body.version).toBe('string')
    expect(body.duration).toBeUndefined()

    expect(take).toEqual({
      id: 'd1',
      title: 'Toma 1',
      public_id: 'erato/compositions/c1/take',
      duration: 36.0065,
      date: '2026-10-01T10:00:00Z',
    })
  })

  it('confirmUpload defaults a missing duration to 0', async () => {
    const spy = vi
      .spyOn(clientModule, 'apiClient')
      .mockResolvedValueOnce(jsonResponse(backendDemo, 201))
    await demosApi.confirmUpload('c1', {
      public_id: 'p',
      version: 1,
      signature: 's',
      title: 't',
    })
    const body = JSON.parse(spy.mock.calls[0][1]!.body as string)
    expect(body.duration_s).toBe(0)
  })

  it('confirmUpload throws a string message from the backend error envelope', async () => {
    vi.spyOn(clientModule, 'apiClient').mockResolvedValueOnce(
      jsonResponse({ error: 'validation', message: 'Firma inválida', detail: [{ loc: ['body'] }] }, 422)
    )
    await expect(
      demosApi.confirmUpload('c1', { public_id: 'p', version: 1, signature: 's', title: 't' })
    ).rejects.toThrow('Firma inválida')
  })

  it('addComment sends timestamp_s and maps the response', async () => {
    const spy = vi
      .spyOn(clientModule, 'apiClient')
      .mockResolvedValueOnce(jsonResponse(backendComment, 201))

    const comment = await demosApi.addComment('c1', 'd1', 'Entra la guitarra', 12.5)

    const body = JSON.parse(spy.mock.calls[0][1]!.body as string)
    expect(body).toEqual({ text: 'Entra la guitarra', timestamp_s: 12.5 })
    expect(comment).toEqual({
      id: 'cm1',
      t: 12.5,
      author: 'Ana',
      text: 'Entra la guitarra',
      created_at: '2026-10-01T10:05:00Z',
    })
  })

  it('listComments maps CommentResponse to DemoComment', async () => {
    vi.spyOn(clientModule, 'apiClient').mockResolvedValueOnce(jsonResponse([backendComment]))
    const list = await demosApi.listComments('c1', 'd1')
    expect(list).toEqual([
      {
        id: 'cm1',
        t: 12.5,
        author: 'Ana',
        text: 'Entra la guitarra',
        created_at: '2026-10-01T10:05:00Z',
      },
    ])
  })

  it.each([[null], [undefined], [''], ['   ']])(
    'listComments falls back to "Usuario" when author_name is %j and never shows the id',
    async (name) => {
      vi.spyOn(clientModule, 'apiClient').mockResolvedValueOnce(
        jsonResponse([{ ...backendComment, author_name: name }])
      )
      const [comment] = await demosApi.listComments('c1', 'd1')
      expect(comment.author).toBe('Usuario')
      expect(comment.author).not.toBe('u1')
    }
  )

  it('addComment falls back to "Usuario" when author_name is missing', async () => {
    const { author_name: _omit, ...withoutName } = backendComment
    vi.spyOn(clientModule, 'apiClient').mockResolvedValueOnce(jsonResponse(withoutName, 201))
    const comment = await demosApi.addComment('c1', 'd1', 'x', 1)
    expect(comment.author).toBe('Usuario')
  })
})

describe('DemosSection take resolution', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  const mountSection = (demos: demosApi.DemoTake[]) =>
    mount(DemosSection, {
      props: { compositionId: 'c1', demos },
      global: { stubs: { ErDemoPlayer: true, DemoUploadModal: true } },
    })

  const playerTakes = (w: ReturnType<typeof mountSection>) =>
    w.findComponent({ name: 'ErDemoPlayer' }).props('takes') as demosApi.DemoTake[]

  it('resolves src and comments for existing demos on mount, tolerating failures', async () => {
    vi.spyOn(demosApi, 'getPlaybackUrl').mockImplementation(async (_c, id) => {
      if (id === 'bad') throw new Error('boom')
      return { url: `https://cdn/${id}.mp3`, expires_at: 1 }
    })
    vi.spyOn(demosApi, 'listComments').mockImplementation(async (_c, id) => {
      if (id === 'bad') throw new Error('boom')
      return [{ t: 1, author: 'Ana', text: 'hola' }]
    })

    const original: demosApi.DemoTake[] = [
      { id: 'ok', title: 'A', public_id: 'p1', duration: 10 },
      { id: 'bad', title: 'B', public_id: 'p2', duration: 20 },
    ]
    const w = mountSection(original)
    await flushPromises()

    const takes = playerTakes(w)
    expect(takes.find((t) => t.id === 'ok')?.src).toBe('https://cdn/ok.mp3')
    expect(takes.find((t) => t.id === 'ok')?.comments).toHaveLength(1)
    expect(takes.find((t) => t.id === 'bad')?.src).toBeUndefined()
    expect(takes.find((t) => t.id === 'bad')?.comments ?? []).toHaveLength(0)
    // props are not mutated
    expect(original[0].src).toBeUndefined()
  })

  it('resolves src and comments for a newly uploaded demo using its mapped id', async () => {
    const urlSpy = vi
      .spyOn(demosApi, 'getPlaybackUrl')
      .mockResolvedValue({ url: 'https://cdn/new.mp3', expires_at: 1 })
    vi.spyOn(demosApi, 'listComments').mockRejectedValue(new Error('boom'))

    const w = mountSection([])
    await flushPromises()
    const modal = { id: 'new', title: 'N', public_id: 'p', duration: 5 }
    ;(w.vm as any).showUploadModal = true
    await flushPromises()
    w.findComponent({ name: 'DemoUploadModal' }).vm.$emit('uploaded', modal)
    await flushPromises()

    expect(urlSpy).toHaveBeenCalledWith('c1', 'new')
    const takes = playerTakes(w)
    expect(takes).toHaveLength(1)
    expect(takes[0].src).toBe('https://cdn/new.mp3')
    expect(w.emitted('updated')).toBeTruthy()
  })
})

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
