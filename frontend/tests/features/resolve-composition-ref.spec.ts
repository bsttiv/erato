import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as compApi from '@/api/compositions'
import { resolveCompositionRef, isObjectIdRef } from '@/features/compositions/resolveCompositionRef'
import type { CompositionResponse } from '@/api/compositions'

const HEX_ID = '64b7f0c2a1b2c3d4e5f60718'
const comp = { id: HEX_ID, title: 'Noche' } as CompositionResponse

describe('isObjectIdRef', () => {
  it('detects 24-char hex refs only', () => {
    expect(isObjectIdRef(HEX_ID)).toBe(true)
    expect(isObjectIdRef('noche-de-otono')).toBe(false)
    expect(isObjectIdRef('64b7f0c2a1b2c3d4e5f6071')).toBe(false)
    expect(isObjectIdRef('zzb7f0c2a1b2c3d4e5f60718')).toBe(false)
  })
})

describe('resolveCompositionRef', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('hex ref resolves by id first', async () => {
    const byId = vi.spyOn(compApi, 'getComposition').mockResolvedValue(comp)
    const bySlug = vi.spyOn(compApi, 'getCompositionBySlug').mockResolvedValue(comp)
    await expect(resolveCompositionRef(HEX_ID)).resolves.toBe(comp)
    expect(byId).toHaveBeenCalledWith(HEX_ID)
    expect(bySlug).not.toHaveBeenCalled()
  })

  it('hex ref falls back to slug only on 404', async () => {
    vi.spyOn(compApi, 'getComposition').mockRejectedValue(new compApi.HttpError('nf', 404))
    const bySlug = vi.spyOn(compApi, 'getCompositionBySlug').mockResolvedValue(comp)
    await expect(resolveCompositionRef(HEX_ID)).resolves.toBe(comp)
    expect(bySlug).toHaveBeenCalledWith(HEX_ID)
  })

  it('hex ref does not fall back on non-404 errors', async () => {
    vi.spyOn(compApi, 'getComposition').mockRejectedValue(new compApi.HttpError('forbidden', 403))
    const bySlug = vi.spyOn(compApi, 'getCompositionBySlug').mockResolvedValue(comp)
    await expect(resolveCompositionRef(HEX_ID)).rejects.toThrow('forbidden')
    expect(bySlug).not.toHaveBeenCalled()
  })

  it('non-hex ref goes straight to by-slug', async () => {
    const byId = vi.spyOn(compApi, 'getComposition').mockResolvedValue(comp)
    const bySlug = vi.spyOn(compApi, 'getCompositionBySlug').mockResolvedValue(comp)
    await resolveCompositionRef('noche-de-otono')
    expect(byId).not.toHaveBeenCalled()
    expect(bySlug).toHaveBeenCalledWith('noche-de-otono')
  })
})
