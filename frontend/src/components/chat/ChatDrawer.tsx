import { useState, useRef, useEffect } from 'react'
import { useChat } from '@/hooks/useChat'
import ChatMessages from '@/components/chat/ChatMessages'
import { Button } from '@/components/ui/button'

export default function ChatDrawer() {
  const [open, setOpen] = useState(false)
  const [input, setInput] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const { messages, streaming, error, sendMessage, abort, clear } = useChat()

  // focus input when drawer opens
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100)
  }, [open])

  const handleSend = () => {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')
    sendMessage(text)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <>
      {/* floating button */}
      <button
        onClick={() => setOpen(true)}
        className={`
          fixed bottom-6 right-6 z-40
          w-14 h-14 rounded-full shadow-lg
          bg-primary text-primary-foreground
          flex items-center justify-center text-2xl
          transition-all duration-200
          hover:scale-105 active:scale-95
          ${open ? 'opacity-0 pointer-events-none' : 'opacity-100'}
        `}
        aria-label="Open chat"
      >
        ⚡
      </button>

      {/* backdrop */}
      {open && (
        <div
          className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        />
      )}

      {/* drawer */}
      <div className={`
        fixed bottom-0 right-0 z-50
        w-full sm:w-[420px] h-[70vh] sm:h-[600px] sm:bottom-6 sm:right-6
        bg-background border border-border
        rounded-t-2xl sm:rounded-2xl shadow-2xl
        flex flex-col
        transition-all duration-300 ease-out
        ${open
          ? 'translate-y-0 opacity-100'
          : 'translate-y-full sm:translate-y-8 opacity-0 pointer-events-none'
        }
      `}>

        {/* header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-border shrink-0">
          <div className="flex items-center gap-2">
            <span className="text-lg">⚡</span>
            <div>
              <p className="text-sm font-medium">Capple Chat</p>
              <p className="text-xs text-muted-foreground">Social battery insights</p>
            </div>
          </div>
          <div className="flex items-center gap-1">
            {messages.length > 0 && (
              <Button variant="ghost" size="sm"
                className="text-xs h-7 px-2 text-muted-foreground"
                onClick={clear}>
                Clear
              </Button>
            )}
            <Button variant="ghost" size="sm"
              className="h-7 w-7 p-0 text-muted-foreground"
              onClick={() => setOpen(false)}>
              ✕
            </Button>
          </div>
        </div>

        {/* messages */}
        <ChatMessages
          messages={messages}
          streaming={streaming}
          error={error}
        />

        {/* input */}
        <div className="px-4 py-3 border-t border-border shrink-0">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your battery trends..."
              rows={1}
              className="
                flex-1 resize-none rounded-xl border border-input
                bg-muted px-3 py-2 text-sm
                placeholder:text-muted-foreground
                focus:outline-none focus:ring-1 focus:ring-ring
                max-h-32 overflow-y-auto
              "
              style={{ fieldSizing: 'content' } as React.CSSProperties}
              disabled={streaming}
            />
            <Button
              size="sm"
              className="h-9 w-9 p-0 rounded-xl shrink-0"
              onClick={streaming ? abort : handleSend}
              disabled={!streaming && !input.trim()}
            >
              {streaming ? '■' : '↑'}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground mt-2 text-center">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </>
  )
}