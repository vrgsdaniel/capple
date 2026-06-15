import { Users, ShoppingCart } from 'lucide-react'
import { useGroceryList } from '@/hooks/useGroceryList'
import { useGroceryRealtime } from '@/hooks/useGroceryRealtime'
import GroceryAddBar from './GroceryAddBar'
import GroceryItem from './GroceryItem'
import HistorySection from './HistorySection'

interface Props {
  householdId: string
}

export default function GroceriesTab({ householdId }: Props) {
  const { list, loading, error, refetch, addItem, markBought, restoreItem, removeItem, clearHistory } =
    useGroceryList()

  useGroceryRealtime(householdId, refetch)

  return (
    <div className="rounded-xl min-h-[400px]" style={{ color: '#ebeeef' }}>
      {/* header */}
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-[#6e7378]">Groceries</p>
        <p className="text-xs text-[#6e7378]">{list.active.length} item{list.active.length !== 1 ? 's' : ''}</p>
      </div>
      <div className="mt-1 flex items-center gap-1.5 text-[#6e7378]">
        <Users size={12} />
        <p className="text-xs">Shared with your household — changes sync live</p>
      </div>

      {/* add bar */}
      <GroceryAddBar onAdd={addItem} />

      {/* error */}
      {error && (
        <p className="mt-4 text-sm text-destructive">{error}</p>
      )}

      {/* loading */}
      {loading && (
        <p className="mt-8 text-center text-sm text-[#4a4f54]">Loading…</p>
      )}

      {/* active list */}
      {!loading && (
        <>
          {list.active.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="mt-4 space-y-0.5">
              {list.active.map(item => (
                <GroceryItem
                  key={item.id}
                  item={item}
                  onMarkBought={markBought}
                  onRemove={removeItem}
                />
              ))}
            </div>
          )}

          {/* recently bought */}
          {list.history.length > 0 && (
            <HistorySection
              items={list.history}
              onReAdd={restoreItem}
              onClearHistory={clearHistory}
            />
          )}
        </>
      )}
    </div>
  )
}

function EmptyState() {
  return (
    <div
      className="mt-6 flex flex-col items-center gap-3 rounded-xl border border-dashed border-[#25292c] py-12 text-center"
    >
      <ShoppingCart size={28} color="#4a4f54" />
      <p className="text-sm text-[#6e7378]">Your list is empty</p>
      <p className="text-xs text-[#4a4f54]">Add an item above or push ingredients from a recipe</p>
    </div>
  )
}
