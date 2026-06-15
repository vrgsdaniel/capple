import { useState } from 'react'
import { Trash2, ChefHat, Check } from 'lucide-react'
import type { GroceryItem as GroceryItemType } from '@/types/groceries'

interface Props {
  item: GroceryItemType
  onMarkBought: (id: string) => Promise<void>
  onRemove: (id: string) => Promise<void>
}

export default function GroceryItem({ item, onMarkBought, onRemove }: Props) {
  const [leaving, setLeaving] = useState(false)
  const [checked, setChecked] = useState(false)

  const handleBuy = () => {
    if (leaving) return
    setChecked(true)
    setLeaving(true)
    setTimeout(() => onMarkBought(item.id), 220)
  }

  return (
    <div
      className="group flex items-center gap-3 rounded-lg px-1 py-2 transition-all duration-[220ms]"
      style={{
        opacity: leaving ? 0 : 1,
        transform: leaving ? 'translateX(8px)' : 'translateX(0)',
        background: 'transparent',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = '#15181a')}
      onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
    >
      {/* check circle */}
      <button
        onClick={handleBuy}
        className="flex shrink-0 items-center justify-center rounded-full transition-all duration-150"
        style={{
          width: 22,
          height: 22,
          border: checked ? 'none' : '1.75px solid #4a4f54',
          background: checked ? '#bdf260' : 'transparent',
        }}
        aria-label="Mark as bought"
      >
        {checked && <Check size={13} strokeWidth={2.5} color="#0e1011" />}
      </button>

      {/* qty + name */}
      <div className="flex flex-1 items-baseline gap-2 min-w-0">
        {item.qty && (
          <span className="shrink-0 text-sm font-medium tabular-nums text-[#a8adb1]">
            {item.qty}
          </span>
        )}
        <span className="truncate text-[14.5px] text-[#ebeeef]">{item.name}</span>
      </div>

      {/* recipe source hint */}
      {item.source_recipe_title && (
        <div className="flex shrink-0 items-center gap-1 text-[#6e7378]">
          <ChefHat size={11} />
          <span className="text-[11.5px] max-w-[100px] truncate">{item.source_recipe_title}</span>
        </div>
      )}

      {/* remove button — revealed on row hover */}
      <button
        onClick={() => onRemove(item.id)}
        className="shrink-0 rounded p-1 opacity-0 transition-all duration-120 group-hover:opacity-100 hover:text-[#ff5e7a]"
        style={{ color: '#4a4f54' }}
        aria-label="Remove item"
      >
        <Trash2 size={15} />
      </button>
    </div>
  )
}
