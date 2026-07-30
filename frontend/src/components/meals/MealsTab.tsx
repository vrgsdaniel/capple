import { useState, useRef, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Search, X, ArrowDownUp, ChevronDown, ChevronLeft, ChevronRight, Check } from 'lucide-react'
import RecipeCard from './RecipeCard'
import RecipeSheet from './RecipeSheet'
import { useRecipes } from '@/hooks/useRecipes'
import { useGroceryList } from '@/hooks/useGroceryList'
import type { RecipeSearchSpec, SortKey } from '@/types/meals'
import { MEAL_TYPES, TIME_BUCKETS, SORT_OPTIONS } from '@/types/meals'
import './meals.css'

interface SortDropdownProps {
  value: SortKey
  onChange: (v: SortKey) => void
  relevanceLabel: string
}

function SortDropdown({ value, onChange, relevanceLabel }: SortDropdownProps) {
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
        <span>Sort: {value === 'relevance' ? relevanceLabel : current?.label}</span>
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
              <span>{opt.value === 'relevance' ? relevanceLabel : opt.label}</span>
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
  const [urlParams, setUrlParams] = useSearchParams()
  const search = urlParams.get('q') ?? ''
  const mealFilters = urlParams
    .getAll('meal')
    .filter((value): value is RecipeSearchSpec['mealTypes'][number] =>
      MEAL_TYPES.some(option => option.value === value),
    )
  const labels = urlParams.getAll('label')
  const ingredients = urlParams.getAll('ingredient')
  const timeParam = Number(urlParams.get('maxTime'))
  const timeMax = TIME_BUCKETS.some(option => option.value === timeParam) ? timeParam : null
  const sortParam = urlParams.get('sort')
  const sort = SORT_OPTIONS.some(option => option.value === sortParam)
    ? (sortParam as SortKey)
    : 'relevance'
  const liked = urlParams.get('liked') === 'true'
  const cooked = urlParams.get('cooked') === 'true'
  const pageParam = Number(urlParams.get('page'))
  const page = Number.isInteger(pageParam) && pageParam > 0 ? pageParam : 1
  const limit = 24
  const searchSpec: RecipeSearchSpec = {
    text: search,
    mealTypes: mealFilters,
    labels,
    ingredients,
    maxTotalMinutes: timeMax,
    liked: liked ? true : null,
    cooked: cooked ? true : null,
    sort,
    page,
    limit,
  }
  const { recipes, total, loading, error, ensureDetails, toggleLike, toggleCooked, rateRecipe } = useRecipes(searchSpec)
  const { addFromRecipe } = useGroceryList()

  const [activeId, setActiveId] = useState<string | null>(null)

  function updateSearchParams(
    update: (next: URLSearchParams) => void,
    options: { resetPage?: boolean; replace?: boolean } = {},
  ) {
    const next = new URLSearchParams(urlParams)
    update(next)
    if (options.resetPage !== false) next.delete('page')
    setUrlParams(next, { replace: options.replace ?? true })
  }

  function toggleMeal(value: RecipeSearchSpec['mealTypes'][number]) {
    updateSearchParams(next => {
      const selected = next.getAll('meal')
      next.delete('meal')
      const updated = selected.includes(value)
        ? selected.filter(item => item !== value)
        : [...selected, value]
      updated.forEach(item => next.append('meal', item))
    })
  }

  function handleOpenRecipe(id: string) {
    setActiveId(id)
    ensureDetails(id)
  }

  const activeRecipe = recipes.find(r => r.id === activeId) ?? null
  const hasFilters = (
    mealFilters.length > 0
    || labels.length > 0
    || ingredients.length > 0
    || timeMax !== null
    || liked
    || cooked
  )

  if (loading && recipes.length === 0) {
    return (
      <div className="meals-tab">
        <div className="meals-empty" style={{ border: 'none' }}>
          <div className="meals-empty-title">Loading recipes…</div>
        </div>
      </div>
    )
  }

  if (error && recipes.length === 0) {
    return (
      <div className="meals-tab">
        <div className="meals-empty" role="alert">
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
              onChange={event => updateSearchParams(next => {
                const value = event.target.value
                if (value) next.set('q', value)
                else next.delete('q')
              })}
            />
            {search && (
              <button
                type="button"
                className="meals-search-clear"
                onClick={() => updateSearchParams(next => next.delete('q'))}
                aria-label="Clear search"
              >
                <X size={14} strokeWidth={1.75} />
              </button>
            )}
          </div>
          <SortDropdown
            value={sort}
            relevanceLabel={search.trim() ? 'Best match' : 'Recommended'}
            onChange={value => updateSearchParams(next => {
              if (value === 'relevance') next.delete('sort')
              else next.set('sort', value)
            })}
          />
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
                onClick={() => toggleMeal(opt.value)}
              >
                <span style={{ filter: 'grayscale(0.3)' }}>{opt.emoji}</span>
                {opt.label}
              </button>
            ))}
          </div>
        </div>

        {/* Row 3: time + personal filters + clear all */}
        <div className="meals-toolbar-row">
          <div className="meals-filter-group">
            <span className="meals-micro">Time</span>
            {TIME_BUCKETS.map(opt => (
              <button
                key={opt.value}
                type="button"
                className={`meals-chip${timeMax === opt.value ? ' active' : ''}`}
                onClick={() => updateSearchParams(next => {
                  if (timeMax === opt.value) next.delete('maxTime')
                  else next.set('maxTime', String(opt.value))
                })}
              >
                {opt.label}
              </button>
            ))}
          </div>
          <div className="meals-filter-group">
            <span className="meals-micro">My recipes</span>
            <button
              type="button"
              className={`meals-chip${liked ? ' active' : ''}`}
              aria-pressed={liked}
              onClick={() => updateSearchParams(next => {
                if (liked) next.delete('liked')
                else next.set('liked', 'true')
              })}
            >
              Liked
            </button>
            <button
              type="button"
              className={`meals-chip${cooked ? ' active' : ''}`}
              aria-pressed={cooked}
              onClick={() => updateSearchParams(next => {
                if (cooked) next.delete('cooked')
                else next.set('cooked', 'true')
              })}
            >
              Already cooked
            </button>
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
                updateSearchParams(next => {
                  next.delete('meal')
                  next.delete('label')
                  next.delete('ingredient')
                  next.delete('maxTime')
                  next.delete('liked')
                  next.delete('cooked')
                })
              }}
            >
              Clear all
              <X size={12} strokeWidth={1.75} />
            </button>
          )}
        </div>
      </div>

      {error && (
        <p className="mb-3 text-sm text-destructive" role="alert">
          {error}. Showing previous results.
        </p>
      )}

      {/* Section head */}
      <div className="meals-section-head">
        <span className="meals-micro">
          {hasFilters || search ? 'Results' : 'All recipes'}
        </span>
        <span className="meals-results-count">
          {total} {total === 1 ? 'recipe' : 'recipes'}
        </span>
      </div>

      {/* Content */}
      {recipes.length === 0 ? (
        <div className="meals-empty">
          <div className="meals-empty-title">No recipes match</div>
          <div>Try clearing some filters or a different search.</div>
        </div>
      ) : (
        <div className="meals-recipe-grid">
          {recipes.map(r => (
            <RecipeCard
              key={r.id}
              recipe={r}
              onOpen={handleOpenRecipe}
              onToggleLike={toggleLike}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {total > limit && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '10px', marginTop: '20px', marginBottom: '20px' }}>
          <button
            type="button"
            className="meals-btn"
            onClick={() => updateSearchParams(
              next => {
                const previous = Math.max(1, page - 1)
                if (previous === 1) next.delete('page')
                else next.set('page', String(previous))
              },
              { resetPage: false, replace: false },
            )}
            disabled={page === 1}
            style={{ opacity: page === 1 ? 0.5 : 1, cursor: page === 1 ? 'not-allowed' : 'pointer' }}
          >
            <ChevronLeft size={16} strokeWidth={1.75} />
            Previous
          </button>
          <span style={{ alignSelf: 'center', color: 'var(--m-fg-3)', fontSize: '14px' }}>
            Page {page}
          </span>
          <button
            type="button"
            className="meals-btn"
            onClick={() => updateSearchParams(
              next => next.set('page', String(page + 1)),
              { resetPage: false, replace: false },
            )}
            disabled={page * limit >= total}
            style={{ opacity: page * limit >= total ? 0.5 : 1, cursor: page * limit >= total ? 'not-allowed' : 'pointer' }}
          >
            Next
            <ChevronRight size={16} strokeWidth={1.75} />
          </button>
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
        onAddToList={addFromRecipe}
      />
    </div>
  )
}
