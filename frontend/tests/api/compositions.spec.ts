import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  listCompositions,
  getComposition,
  getCompositionBySlug,
  createComposition,
  updateComposition,
  updateChordsSection,
  updateTablatureSection,
  updateLyricsSection,
  updateTodosSection,
} from '@/api/compositions'
import type {
  ChordsSection,
  TablatureSection,
  LyricsSection,
  TodoItem,
} from '@/api/compositions'

describe('Compositions API client contract', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('listCompositions() calls GET /compositions and returns flat CompositionListItem[]', async () => {
    const mockList = [
      {
        id: 'comp-1',
        owner_id: 'user-1',
        title: 'Song One',
        visibility: 'public',
        created_at: '2026-10-01T12:00:00Z',
        updated_at: '2026-10-01T12:00:00Z',
      },
      {
        id: 'comp-2',
        owner_id: 'user-1',
        title: 'Song Two',
        visibility: 'private',
        created_at: '2026-10-01T12:00:00Z',
        updated_at: '2026-10-01T12:00:00Z',
      },
    ]

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockList), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await listCompositions()

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions')
    expect(init?.method).toBeUndefined() // default GET
    expect(result).toEqual(mockList)
    expect(result[0].visibility).toBe('public')
  })

  it('getComposition(id) calls GET /compositions/{id} and returns CompositionResponse with typed sections and user_role', async () => {
    const mockDetail = {
      id: 'comp-1',
      owner_id: 'user-1',
      title: 'Song One',
      visibility: 'public',
      share_slug: 'song-one-xyz',
      chords: {
        instrument: 'guitar',
        entries: [{ bar: 1, notes: [0, 2, 2, 1, 0, 0], name: 'E' }],
      },
      tablature: {
        tabs: [{ id: 'tab-1', title: 'Intro', strings: 6, columns: [['0', '', '', '', '', '']] }],
      },
      lyrics: {
        content: '[E]Hello world',
      },
      todos: [{ text: 'Record intro', done: false }],
      demos: [
        {
          demo_id: 'd-1',
          cloudinary_public_id: 'c-1',
          title: 'Demo 1',
          duration_s: 120.5,
          uploaded_by: 'user-1',
          uploaded_at: '2026-10-01T12:00:00Z',
        },
      ],
      members: [{ user_id: 'user-2', role: 'editor' }],
      user_role: 'owner',
      created_at: '2026-10-01T12:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockDetail), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await getComposition('comp-1')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1')
    expect(result.id).toBe('comp-1')
    expect(result.visibility).toBe('public')
    expect(result.share_slug).toBe('song-one-xyz')
    expect(result.user_role).toBe('owner')
    expect(result.chords?.entries[0].name).toBe('E')
    expect(result.tablature?.tabs[0].title).toBe('Intro')
    expect(result.lyrics?.content).toBe('[E]Hello world')
    expect(result.todos[0].text).toBe('Record intro')
    expect(result.demos?.[0]?.title).toBe('Demo 1')
  })

  it('getCompositionBySlug(slug) calls GET /compositions/by-slug/{slug}', async () => {
    const mockDetail = {
      id: 'comp-1',
      owner_id: 'user-1',
      title: 'Song One',
      visibility: 'public',
      share_slug: 'song-one-xyz',
      todos: [],
      demos: [],
      members: [],
      created_at: '2026-10-01T12:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockDetail), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await getCompositionBySlug('song-one-xyz')

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/by-slug/song-one-xyz')
    expect(result.share_slug).toBe('song-one-xyz')
  })

  it('createComposition(payload) calls POST /compositions with CreateCompositionPayload', async () => {
    const payload = {
      title: 'New Track',
      visibility: 'private' as const,
      key: 'Am',
      bpm: 120,
    }

    const mockResponse = {
      id: 'comp-new',
      owner_id: 'user-1',
      title: 'New Track',
      visibility: 'private',
      todos: [],
      demos: [],
      members: [],
      created_at: '2026-10-01T12:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockResponse), {
        status: 201,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await createComposition(payload)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions')
    expect(init?.method).toBe('POST')
    expect(JSON.parse(init?.body as string)).toEqual({
      title: 'New Track',
      visibility: 'private',
      key: 'Am',
      bpm: 120,
    })
    expect(result.id).toBe('comp-new')
  })

  it('updateComposition(id, payload) calls PATCH /compositions/{id}', async () => {
    const payload = {
      title: 'Updated Track',
      bpm: 128,
    }

    const mockResponse = {
      id: 'comp-1',
      owner_id: 'user-1',
      title: 'Updated Track',
      visibility: 'private',
      bpm: 128,
      todos: [],
      demos: [],
      members: [],
      created_at: '2026-10-01T12:00:00Z',
      updated_at: '2026-10-01T12:00:00Z',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(mockResponse), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await updateComposition('comp-1', payload)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1')
    expect(init?.method).toBe('PATCH')
    expect(JSON.parse(init?.body as string)).toEqual(payload)
    expect(result.title).toBe('Updated Track')
  })

  it('updateChordsSection(id, payload) calls PUT /api/compositions/{id}/chords', async () => {
    const chords: ChordsSection = {
      instrument: 'guitar',
      entries: [{ bar: 1, notes: [0, 2, 2, 0, 0, 0], name: 'Em' }],
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(chords), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await updateChordsSection('comp-1', chords)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/chords')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(init?.body as string)).toEqual(chords)
    expect(result).toEqual(chords)
  })

  it('updateTablatureSection(id, payload) calls PUT /api/compositions/{id}/tablature', async () => {
    const tablature: TablatureSection = {
      tabs: [{ id: 'tab-1', title: 'Solo', strings: 6, columns: [['12', '', '', '', '', '']] }],
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(tablature), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await updateTablatureSection('comp-1', tablature)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/tablature')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(init?.body as string)).toEqual(tablature)
    expect(result).toEqual(tablature)
  })

  it('updateLyricsSection(id, payload) calls PUT /api/compositions/{id}/lyrics', async () => {
    const lyrics: LyricsSection = {
      content: '# Verso 1\n[Am]Letra nueva',
    }

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(lyrics), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await updateLyricsSection('comp-1', lyrics)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/lyrics')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(init?.body as string)).toEqual(lyrics)
    expect(result).toEqual(lyrics)
  })

  it('updateTodosSection(id, payload) calls PUT /api/compositions/{id}/todos with a bare array', async () => {
    const todos: TodoItem[] = [
      { text: 'Afinar bajo', done: true },
      { text: 'Probar reverb', done: false },
    ]

    const fetchSpy = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(
      new Response(JSON.stringify(todos), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      })
    )

    const result = await updateTodosSection('comp-1', todos)

    expect(fetchSpy).toHaveBeenCalledTimes(1)
    const [url, init] = fetchSpy.mock.calls[0]
    expect(url.toString()).toContain('/api/compositions/comp-1/todos')
    expect(init?.method).toBe('PUT')
    expect(JSON.parse(init?.body as string)).toEqual(todos)
    expect(result).toEqual(todos)
  })
})
