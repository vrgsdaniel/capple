import { useState } from 'react'
import { ShoppingCart, ChevronDown, RotateCcw } from 'lucide-react'
import type { GroceryItem } from '@/types/groceries'

interface Props {
  items: GroceryItem[]
  onReAdd: (id: string) => Promise<void>
  onClearHistory: () => Promise<void>
}

function relativeTime(dateStr: string): string {
  const diff = Math.floor((Date.now() - new Date(dateStr).getTime()) / 86_400_000)
  if (diff === 0) return 'Today'
  if (diff === 1) return 'Yesterday'
  if (diff < 7) return `${diff} days ago`
  return new Date(dateStr).toLocaleDateString()
}

export default function HistorySection({ items, onReAdd, onClearHistory }: Props) {
  const [open, setOpen] = useState(false)
  const [clearing, setClearing] = useState(false)

  const handleClear = async () => {
    if (!window.confirm('Clear all recently bought items?')) return
    setClearing(true)
    try {
      await onClearHistory()
    } finally {
      setClearing(false)
    }
  }

  return (
    <div className="mt-6 border-t border-[#25292c] pt-4">
      {/* collapsible header */}
      <div className="flex w-full items-center gap-2 text-[#6e7378]">
        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          className="flex min-w-0 flex-1 items-center gap-2 text-left hover:text-[#a8adb1] transition-colors"
        >
          <ShoppingCart size={14} />
          <span className="text-sm">Recently bought · {items.length}</span>
          <ChevronDown
            size={14}
            className="ml-auto transition-transform duration-150"
            style={{ transform: open ? 'rotate(180deg)' : 'rotate(0deg)' }}
          />
        </button>
        {open && (
          <button
            type="button"
            onClick={handleClear}
            disabled={clearing}
            className="ml-2 text-xs text-[#6e7378] hover:text-[#ff5e7a] transition-colors disabled:opacity-40"
          >
            Clear
          </button>
        )}
      </div>

      {/* history rows */}
      {open && (
        <div className="mt-3 space-y-1">
          {items.map(item => (
            <HistoryRow key={item.id} item={item} onReAdd={onReAdd} />
          ))}
        </div>
      )}
    </div>
  )
}

function HistoryRow({ item, onReAdd }: { item: GroceryItem; onReAdd: (id: string) => Promise<void> }) {
  const [loading, setLoading] = useState(false)

  const handleReAdd = async () => {
    setLoading(true)
    try {
      await onReAdd(item.id)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="group flex items-center gap-3 rounded-lg px-1 py-2 transition-colors hover:bg-[#15181a]">
      <div className="flex flex-1 items-baseline gap-2 min-w-0">
        {item.qty && (
          <span className="shrink-0 text-sm tabular-nums text-[#4a4f54] line-through">
            {item.qty}
          </span>
        )}
        <span className="truncate text-sm text-[#6e7378] line-through">{item.name}</span>
      </div>

      {item.bought_at && (
        <span className="shrink-0 text-xs text-[#4a4f54]">{relativeTime(item.bought_at)}</span>
      )}

      <button
        onClick={handleReAdd}
        disabled={loading}
        className="shrink-0 rounded p-1 text-[#4a4f54] opacity-0 transition-all duration-120 group-hover:opacity-100 hover:text-[#bdf260] disabled:opacity-40"
        aria-label="Add back to list"
      >
        <RotateCcw size={14} />
      </button>
    </div>
  )
}
