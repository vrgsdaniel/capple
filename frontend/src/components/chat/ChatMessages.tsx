import { useEffect, useRef } from 'react'
import type { Message } from '@/types/chat'

interface Props {
  messages: Message[]
  streaming: boolean
  error: string | null
}

export default function ChatMessages({ messages, streaming, error }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center gap-2 px-6">
        <span className="text-3xl">⚡</span>
        <p className="text-sm text-muted-foreground text-center">
          Ask about your social battery trends, how you're both doing, or whether you need more quality time.
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
      {messages.map((msg, i) => (
        <div
          key={i}
          className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
        >
          <div
            className={`
              max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed
              ${msg.role === 'user'
                ? 'bg-primary text-primary-foreground rounded-br-sm'
                : 'bg-muted text-foreground rounded-bl-sm'
              }
            `}
          >
            {msg.content || (
              streaming && msg.role === 'assistant'
                ? <span className="animate-pulse">···</span>
                : null
            )}
          </div>
        </div>
      ))}

      {error && (
        <p className="text-destructive text-xs text-center">{error}</p>
      )}

      <div ref={bottomRef}/>
    </div>
  )
}