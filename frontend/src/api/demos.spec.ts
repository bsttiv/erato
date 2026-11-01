import { afterEach, describe, expect, it, vi } from 'vitest'
import { StorageError, uploadToStorage, type UploadTarget } from './demos'
import { uploadMessage } from './messages'

const target: UploadTarget = {
  upload_url: 'https://api.cloudinary.com/v1_1/erato/video/upload',
  fields: { api_key: 'key', timestamp: 1700000000, signature: 'signed', public_id: 'erato/songs/1/2/3', type: 'authenticated' },
}
const file = new File(['audio'], 'take.mp3', { type: 'audio/mpeg' })

/** XMLHttpRequest stand-in that records the request and lets each test finish it. */
function fakeXhr() {
  const xhr = {
    upload: {} as { onprogress?: (event: Partial<ProgressEvent>) => void },
    status: 0,
    onload: undefined as undefined | (() => void),
    onerror: undefined as undefined | (() => void),
    open: vi.fn(),
    send: vi.fn(),
  }
  vi.stubGlobal('XMLHttpRequest', function () { return xhr })
  return xhr
}

afterEach(() => vi.unstubAllGlobals())

describe('direct upload to Cloudinary', () => {
  it('CLD-101 posts every signed field plus the file and reports progress', async () => {
    const xhr = fakeXhr()
    const progress: number[] = []
    const upload = uploadToStorage(target, file, (fraction) => progress.push(fraction))
    xhr.upload.onprogress!({ lengthComputable: true, loaded: 0, total: 4 })
    xhr.upload.onprogress!({ lengthComputable: true, loaded: 4, total: 4 })
    xhr.status = 200
    xhr.onload!()
    await upload
    expect(xhr.open).toHaveBeenCalledWith('POST', target.upload_url)
    const form = xhr.send.mock.calls[0][0] as FormData
    for (const [name, value] of Object.entries(target.fields)) expect(form.get(name)).toBe(String(value))
    expect((form.get('file') as File).name).toBe('take.mp3')
    expect(progress).toEqual([0, 1])
  })

  it('CLD-102 rejects with the storage message when Cloudinary refuses', async () => {
    const xhr = fakeXhr()
    const upload = uploadToStorage(target, file, () => {})
    xhr.status = 400
    xhr.onload!()
    const failure = await upload.catch((cause) => cause)
    expect(failure).toBeInstanceOf(StorageError)
    expect(uploadMessage(failure)).toBe('No se pudo subir el archivo. Revisa tu conexión e inténtalo de nuevo.')
  })

  it('CLD-103 explains that demos are unavailable', () => {
    expect(uploadMessage({ status: 503, code: 'storage_unavailable' })).toBe('Las demos no están disponibles en este momento.')
  })
})
