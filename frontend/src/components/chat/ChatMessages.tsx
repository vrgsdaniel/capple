import { Fragment, useEffect, useRef } from 'react'
import type { Message } from '@/types/chat'

interface Props {
  messages: Message[]
  streaming: boolean
  error: string | null
}

function normalizeAssistantContent(content: string): string {
  return content
    .replace(/\r\n?/g, '\n')
    .replace(/\s-\s(?=[A-Z*])/g, '\n- ')
    .replace(/\s(\*\*[^*]+:\*\*)/g, '\n$1')
}

function renderInlineFormatting(text: string) {
  const chunks = text.split(/(\*\*[^*]+\*\*)/g)

  return chunks.map((chunk, idx) => {
    if (chunk.startsWith('**') && chunk.endsWith('**') && chunk.length > 4) {
      return <strong key={`strong-${idx}`}>{chunk.slice(2, -2)}</strong>
    }

    return <Fragment key={`text-${idx}`}>{chunk}</Fragment>
  })
}

function AssistantMessageContent({ content }: { content: string }) {
  const normalized = normalizeAssistantContent(content)
  const lines = normalized.split('\n').map(line => line.trim()).filter(Boolean)
  const blocks: Array<{ type: 'paragraph' | 'list'; items: string[] }> = []

  for (const line of lines) {
    const isListItem = line.startsWith('- ')

    if (isListItem) {
      const item = line.slice(2).trim()
      const lastBlock = blocks[blocks.length - 1]

      if (lastBlock && lastBlock.type === 'list') {
        lastBlock.items.push(item)
      } else {
        blocks.push({ type: 'list', items: [item] })
      }

      continue
    }

    blocks.push({ type: 'paragraph', items: [line] })
  }

  return (
    <div className="space-y-2.5">
      {blocks.map((block, index) => {
        if (block.type === 'list') {
          return (
            <ul key={`list-${index}`} className="list-disc pl-5 space-y-1.5 marker:text-muted-foreground">
              {block.items.map((item, itemIndex) => (
                <li key={`list-item-${index}-${itemIndex}`}>{renderInlineFormatting(item)}</li>
              ))}
            </ul>
          )
        }

        return (
          <p key={`paragraph-${index}`} className="leading-6">
            {renderInlineFormatting(block.items[0])}
          </p>
        )
      })}
    </div>
  )
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
              max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed break-words
              ${msg.role === 'user'
                ? 'bg-primary text-primary-foreground rounded-br-sm'
                : 'bg-muted text-foreground rounded-bl-sm'
              }
            `}
          >
            {msg.content
              ? (msg.role === 'assistant'
                ? <AssistantMessageContent content={msg.content} />
                : <p className="whitespace-pre-wrap">{msg.content}</p>)
              : (streaming && msg.role === 'assistant'
                ? <span className="animate-pulse">···</span>
                : null)}
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