import { fireEvent, render, screen } from '@testing-library/react'
import ChatDrawer from '@/components/chat/ChatDrawer'
import { useChat } from '@/hooks/useChat'
import type { Message } from '@/types/chat'

jest.mock('@/hooks/useChat', () => ({
  useChat: jest.fn(),
}))

const mockedUseChat = useChat as jest.MockedFunction<typeof useChat>

function setUseChatState(params?: {
  messages?: Message[]
  streaming?: boolean
  error?: string | null
  sendMessage?: jest.Mock
  abort?: jest.Mock
  clear?: jest.Mock
}) {
  mockedUseChat.mockReturnValue({
    messages: params?.messages ?? [],
    streaming: params?.streaming ?? false,
    error: params?.error ?? null,
    sendMessage: params?.sendMessage ?? jest.fn(async () => undefined),
    abort: params?.abort ?? jest.fn(),
    clear: params?.clear ?? jest.fn(),
  })
}

describe('ChatDrawer', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('sends message on Enter and not on Shift+Enter', () => {
    const sendMessage = jest.fn(async () => undefined)
    setUseChatState({ sendMessage })

    render(<ChatDrawer />)

    fireEvent.click(screen.getByLabelText('Open chat'))

    const textarea = screen.getByPlaceholderText('Ask about your battery trends...')
    fireEvent.change(textarea, { target: { value: 'hello' } })

    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: true })
    expect(sendMessage).not.toHaveBeenCalled()

    fireEvent.keyDown(textarea, { key: 'Enter', code: 'Enter', shiftKey: false })
    expect(sendMessage).toHaveBeenCalledWith('hello')
  })

  it('calls abort when streaming and send button is pressed', () => {
    const abort = jest.fn()
    setUseChatState({ streaming: true, abort })

    render(<ChatDrawer />)

    fireEvent.click(screen.getByLabelText('Open chat'))

    fireEvent.click(screen.getByRole('button', { name: '■' }))
    expect(abort).toHaveBeenCalledTimes(1)
  })

  it('shows clear button when messages exist and triggers clear', () => {
    const clear = jest.fn()
    setUseChatState({
      messages: [{ role: 'assistant', content: 'hi' }],
      clear,
    })

    render(<ChatDrawer />)

    fireEvent.click(screen.getByLabelText('Open chat'))
    fireEvent.click(screen.getByRole('button', { name: 'Clear' }))

    expect(clear).toHaveBeenCalledTimes(1)
  })
})
