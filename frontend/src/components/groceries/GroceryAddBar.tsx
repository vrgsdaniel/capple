import { useState, useRef } from 'react'

interface Props {
  onAdd: (name: string, qty: string | null) => Promise<void>
}

export default function GroceryAddBar({ onAdd }: Props) {
  const [name, setName] = useState('')
  const [qty, setQty] = useState('')
  const [loading, setLoading] = useState(false)
  const nameRef = useRef<HTMLInputElement>(null)

  const submit = async () => {
    const trimmed = name.trim()
    if (!trimmed || loading) return
    setLoading(true)
    try {
      await onAdd(trimmed, qty.trim() || null)
      setName('')
      setQty('')
      nameRef.current?.focus()
    } finally {
      setLoading(false)
    }
  }

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') submit()
  }

  return (
    <div className="flex gap-2 mt-4">
      <input
        type="text"
        placeholder="Qty"
        value={qty}
        onChange={e => setQty(e.target.value)}
        onKeyDown={onKeyDown}
        className="w-[104px] shrink-0 rounded-lg border border-[#25292c] bg-[#1a1d1f] px-3 py-2 text-sm text-[#ebeeef] placeholder:text-[#4a4f54] focus:outline-none focus:border-[#bdf260]"
      />
      <input
        ref={nameRef}
        type="text"
        placeholder="Item name"
        value={name}
        onChange={e => setName(e.target.value)}
        onKeyDown={onKeyDown}
        className="flex-1 rounded-lg border border-[#25292c] bg-[#1a1d1f] px-3 py-2 text-sm text-[#ebeeef] placeholder:text-[#4a4f54] focus:outline-none focus:border-[#bdf260]"
      />
      <button
        onClick={submit}
        disabled={!name.trim() || loading}
        className="shrink-0 rounded-lg bg-[#bdf260] px-4 py-2 text-sm font-medium text-[#0e1011] transition-opacity disabled:opacity-40 hover:opacity-90"
      >
        Add
      </button>
    </div>
  )
}
