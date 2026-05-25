import { act, renderHook, waitFor } from '@testing-library/react'
import { useChat } from '@/hooks/useChat'
import { supabase } from '@/lib/supabase'

jest.mock('@/lib/env', () => ({
  API_BASE_URL: 'http://localhost:8080',
}))

jest.mock('@/lib/supabase', () => ({
  supabase: {
    auth: {
      getSession: jest.fn(),
    },
  },
}))

type SessionResult = { data: { session: { access_token: string } | null } }

const mockedSupabase = supabase as unknown as {
  auth: {
    getSession: jest.Mock<Promise<SessionResult>>
  }
}

function buildStreamFromChunks(chunks: string[]) {
  const encoder = new TextEncoder()
  let index = 0

  return {
    getReader: () => ({
      read: jest.fn(async () => {
        if (index >= chunks.length) {
          return { done: true, value: undefined }
        }

        const value = encoder.encode(chunks[index])
        index += 1

        return { done: false, value }
      }),
    }),
  }
}

describe('useChat', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    global.fetch = jest.fn()
  })

  it('streams assistant content chunks', async () => {
    mockedSupabase.auth.getSession.mockResolvedValue({
      data: { session: { access_token: 'token-123' } },
    })

    ;(global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      body: buildStreamFromChunks([
        'data: "Hello"\n',
        'data: " world"\n',
        'data: "[DONE]"\n',
      ]),
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Hi there')
    })

    await waitFor(() => {
      expect(result.current.streaming).toBe(false)
    })

    expect(result.current.error).toBeNull()
    expect(result.current.messages).toEqual([
      { role: 'user', content: 'Hi there' },
      { role: 'assistant', content: 'Hello world' },
    ])

    expect(global.fetch).toHaveBeenCalledWith(
      'http://localhost:8080/api/chat',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer token-123',
        }),
      }),
    )
  })

  it('sets error and removes assistant placeholder when session is missing', async () => {
    mockedSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('Need help')
    })

    expect(result.current.streaming).toBe(false)
    expect(result.current.error).toBe('Could not reach the chat. Is the backend running?')
    expect(result.current.messages).toEqual([{ role: 'user', content: 'Need help' }])
    expect(global.fetch).not.toHaveBeenCalled()
  })

  it('clears messages and errors', async () => {
    mockedSupabase.auth.getSession.mockResolvedValue({
      data: { session: null },
    })

    const { result } = renderHook(() => useChat())

    await act(async () => {
      await result.current.sendMessage('test clear')
    })

    expect(result.current.messages.length).toBeGreaterThan(0)
    expect(result.current.error).not.toBeNull()

    act(() => {
      result.current.clear()
    })

    expect(result.current.messages).toEqual([])
    expect(result.current.error).toBeNull()
  })
})
