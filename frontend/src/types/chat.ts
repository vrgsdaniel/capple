export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatContextValue {
  messages: Message[]
  streaming: boolean
  error: string | null
  sendMessage: (text: string) => Promise<void>
  abort: () => void
  clear: () => void
}
