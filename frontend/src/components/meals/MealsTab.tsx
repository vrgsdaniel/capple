import { useState, useMemo, useRef, useEffect } from 'react'
import { Search, X, ArrowDownUp, ChevronDown, Check } from 'lucide-react'
import RecipeCard from './RecipeCard'
import RecipeSheet from './RecipeSheet'
import { useRecipes } from '@/hooks/useRecipes'
import type { SortKey } from '@/types/meals'
import { MEAL_TYPES, DIFFICULTIES, TIME_BUCKETS, SORT_OPTIONS, fuzzyMatch } from '@/types/meals'
import './meals.css'

interface SortDropdownProps {
  value: SortKey
  onChange: (v: SortKey) => void
}

function SortDropdown({ value, onChange }: SortDropdownProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handler(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const current = SORT_OPTIONS.find(s => s.value === value)

  return (
    <div className="meals-sort-wrap" ref={ref}>
      <button
        type="button"
        className={`meals-btn${open ? ' active' : ''}`}
        onClick={() => setOpen(!open)}
      >
        <ArrowDownUp size={13} strokeWidth={1.75} />
        <span>Sort: {current?.label}</span>
        <ChevronDown size={13} strokeWidth={1.75} />
      </button>
      {open && (
        <div className="meals-sort-menu">
          {SORT_OPTIONS.map(opt => (
            <button
              key={opt.value}
              type="button"
              className={value === opt.value ? 'active' : ''}
              onClick={() => {
                onChange(opt.value)
                setOpen(false)
              }}
            >
              <span>{opt.label}</span>
              <span className="meals-sort-check">
                <Check size={14} strokeWidth={1.75} />
              </span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

export default function MealsTab() {
  const { recipes, loading, error, ensureDetails, toggleLike, toggleCooked, rateRecipe } = useRecipes()

  const [search, setSearch] = useState('')
  const [mealFilters, setMealFilters] = useState<string[]>([])
  const [diffFilters, setDiffFilters] = useState<string[]>([])
  const [timeMax, setTimeMax] = useState<number | null>(null)
  const [sort, setSort] = useState<SortKey>('default')
  const [activeId, setActiveId] = useState<string | null>(null)

  function toggleArr(arr: string[], setArr: (v: string[]) => void, v: string) {
    setArr(arr.includes(v) ? arr.filter(x => x !== v) : [...arr, v])
  }

  function handleOpenRecipe(id: string) {
    setActiveId(id)
    ensureDetails(id)
  }

  const filtered = useMemo(() => {
    let out = recipes.filter(r => {
      if (!fuzzyMatch(`${r.title} ${r.tags.join(' ')} ${r.mealType}`, search))
        return false
      if (mealFilters.length > 0 && !mealFilters.includes(r.mealType)) return false
      if (diffFilters.length > 0 && !diffFilters.includes(r.difficulty)) return false
      if (timeMax !== null && r.time > timeMax) return false
      return true
    })
    switch (sort) {
      case 'fastest':
        out = [...out].sort((a, b) => a.time - b.time)
        break
      case 'rating':
        out = [...out].sort((a, b) => b.rating - a.rating)
        break
      case 'cooked':
        out = [...out].sort((a, b) => (b.cookedCount || 0) - (a.cookedCount || 0))
        break
      case 'recent':
        out = [...out].sort((a, b) =>
          (b.lastCooked || '').localeCompare(a.lastCooked || ''),
        )
        break
    }
    return out
  }, [recipes, search, mealFilters, diffFilters, timeMax, sort])

  const activeRecipe = recipes.find(r => r.id === activeId) ?? null
  const hasFilters = mealFilters.length > 0 || diffFilters.length > 0 || timeMax !== null

  if (loading) {
    return (
      <div className="meals-tab">
        <div className="meals-empty" style={{ border: 'none' }}>
          <div className="meals-empty-title">Loading recipes…</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="meals-tab">
        <div className="meals-empty">
          <div className="meals-empty-title">Could not load recipes</div>
          <div>{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="meals-tab">
      {/* Toolbar */}
      <div className="meals-toolbar">
        {/* Row 1: search + sort */}
        <div className="meals-toolbar-row">
          <div className="meals-search-wrap">
            <span className="meals-search-icon">
              <Search size={16} strokeWidth={1.75} />
            </span>
            <input
              className="meals-input"
              type="text"
              placeholder="Search recipes — title, tag, anything…"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
            {search && (
              <button
                type="button"
                className="meals-search-clear"
                onClick={() => setSearch('')}
                aria-label="Clear search"
              >
                <X size={14} strokeWidth={1.75} />
              </button>
            )}
          </div>
          <SortDropdown value={sort} onChange={setSort} />
        </div>

        {/* Row 2: meal filter chips */}
        <div className="meals-toolbar-row">
          <div className="meals-filter-group">
            <span className="meals-micro">Meal</span>
            {MEAL_TYPES.map(opt => (
              <button
                key={opt.value}
                type="button"
                className={`meals-chip${mealFilters.includes(opt.value) ? ' active' : ''}`}
                onClick={() => toggleArr(mealFilters, setMealFilters, opt.value)}
              >
                <span style={{ filter: 'grayscale(0.3)' }}>{opt.emoji}</span>
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Row 3: difficulty + time + clear all */}
        <div className="meals-toolbar-row">
          <div className="meals-filter-group">
            <span className="meals-micro">Difficulty</span>
            {DIFFICULTIES.map(opt => (
              <button
                key={opt.value}
                type="button"
                className={`meals-chip${diffFilters.includes(opt.value) ? ' active' : ''}`}
                onClick={() => toggleArr(diffFilters, setDiffFilters, opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div className="meals-filter-group">
            <span className="meals-micro">Time</span>
            {TIME_BUCKETS.map(opt => (
              <button
                key={opt.value}
                type="button"
                className={`meals-chip${timeMax === opt.value ? ' active' : ''}`}
                onClick={() => setTimeMax(timeMax === opt.value ? null : opt.value)}
              >
                {opt.label}
              </button>
            ))}
          </div>
          {hasFilters && (
            <button
              type="button"
              className="meals-btn ghost"
              style={{
                marginLeft: 'auto',
                color: 'var(--m-fg-3)',
                padding: '5px 10px',
                fontSize: 12,
              }}
              onClick={() => {
                setMealFilters([])
                setDiffFilters([])
                setTimeMax(null)
              }}
            >
              Clear all
              <X size={12} strokeWidth={1.75} />
            </button>
          )}
        </div>
      </div>

      {/* Section head */}
      <div className="meals-section-head">
        <span className="meals-micro">
          {hasFilters || search ? 'Results' : 'All recipes'}
        </span>
        <span className="meals-results-count">
          {filtered.length} of {recipes.length}
        </span>
      </div>

      {/* Content */}
      {filtered.length === 0 ? (
        <div className="meals-empty">
          <div className="meals-empty-title">No recipes match</div>
          <div>Try clearing some filters or a different search.</div>
        </div>
      ) : (
        <div className="meals-recipe-grid">
          {filtered.map(r => (
            <RecipeCard
              key={r.id}
              recipe={r}
              onOpen={handleOpenRecipe}
              onToggleLike={toggleLike}
            />
          ))}
        </div>
      )}

      {/* Detail sheet */}
      <RecipeSheet
        recipe={activeRecipe}
        open={!!activeId}
        onClose={() => setActiveId(null)}
        onToggleLike={toggleLike}
        onToggleCooked={toggleCooked}
        onRate={rateRecipe}
      />
    </div>
  )
}
