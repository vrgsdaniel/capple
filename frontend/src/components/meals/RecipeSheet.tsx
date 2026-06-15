import { useEffect, useState } from 'react'
import { X, Clock, Users, Star, Heart, ChefHat, Share2, ExternalLink, ShoppingCart, Plus, Check } from 'lucide-react'
import { StarInput } from './StarRating'
import type { Recipe } from '@/types/meals'

interface HeroThumbProps {
  recipe: Recipe
}

function HeroThumb({ recipe }: HeroThumbProps) {
  const [errored, setErrored] = useState(false)

  if (errored || !recipe.image) {
    return (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: 72,
        }}
      >
        <span>{recipe.emoji}</span>
      </div>
    )
  }

  return (
    <img
      src={recipe.image}
      alt=""
      style={{ width: '100%', height: '100%', objectFit: 'cover', display: 'block' }}
      onError={() => setErrored(true)}
    />
  )
}

interface Props {
  recipe: Recipe | null
  open: boolean
  onClose: () => void
  onToggleLike: (id: string) => void
  onToggleCooked: (id: string) => void
  onRate: (id: string, rating: number) => void
  onAddToList?: (recipeId: string, ingredients: { name: string; qty?: string }[]) => Promise<void>
}

export default function RecipeSheet({ recipe, open, onClose, onToggleLike, onToggleCooked, onRate, onAddToList }: Props) {
  // Co-locate recipe ID with grocery state so we can derive a reset at render time
  // without needing a setState-in-effect.
  const [groceryState, setGroceryState] = useState<{
    recipeId: string | null
    listStatus: 'idle' | 'loading' | 'done'
    addedIngredients: Set<number>
  }>({ recipeId: null, listStatus: 'idle', addedIngredients: new Set() })

  const currentRecipeId = recipe?.id ?? null
  const gs = groceryState.recipeId === currentRecipeId
    ? groceryState
    : { recipeId: currentRecipeId, listStatus: 'idle' as const, addedIngredients: new Set<number>() }

  const setListStatus = (listStatus: 'idle' | 'loading' | 'done') =>
    setGroceryState(prev => ({ ...prev, recipeId: currentRecipeId, listStatus }))
  const setAddedIngredients = (fn: (prev: Set<number>) => Set<number>) =>
    setGroceryState(prev => ({ ...prev, recipeId: currentRecipeId, addedIngredients: fn(prev.addedIngredients) }))

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    if (open) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!recipe) return null
  const r = recipe

  const lastCookedLabel = r.lastCooked
    ? new Date(r.lastCooked).toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric',
      })
    : null

  return (
    <>
      <div
        className={`meals-scrim${open ? ' open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={`meals-sheet${open ? ' open' : ''}`}
        aria-hidden={!open}
        aria-label={r.title}
      >
        {/* Hero */}
        <div className="meals-sheet-hero">
          <HeroThumb recipe={r} />
          <button
            type="button"
            className="meals-sheet-close"
            onClick={onClose}
            aria-label="Close"
          >
            <X size={18} strokeWidth={1.75} />
          </button>
        </div>

        {/* Body */}
        <div className="meals-sheet-body">
          {/* Tags */}
          <div className="meals-sheet-tags">
            <span className="meals-detail-tag">{r.mealType}</span>
            <span className="meals-detail-tag">{r.difficulty}</span>
            {r.tags.slice(0, 3).map(tag => (
              <span
                key={tag}
                className="meals-detail-tag"
                style={{ background: 'transparent' }}
              >
                {tag}
              </span>
            ))}
          </div>

          {/* Title */}
          <h1 className="meals-sheet-title">{r.title}</h1>

          {/* Meta */}
          <div className="meals-sheet-meta">
            <span className="meals-sheet-meta-item">
              <Clock size={14} strokeWidth={1.75} />
              {r.time} min
            </span>
            <span style={{ color: 'var(--m-fg-4)' }}>·</span>
            <span className="meals-sheet-meta-item">
              <Users size={14} strokeWidth={1.75} />
              {r.servings} servings
            </span>
            <span style={{ color: 'var(--m-fg-4)' }}>·</span>
            <span
              className="meals-sheet-meta-item"
              style={{ color: 'var(--m-accent)' }}
            >
              <Star size={13} strokeWidth={1.75} fill="currentColor" />
              {r.rating.toFixed(1)}
            </span>
          </div>

          {/* Description */}
          {r.description && (
            <p className="meals-sheet-description">{r.description}</p>
          )}

          {/* Action strip */}
          <div className="meals-action-strip">
            <button
              type="button"
              className={`meals-action-btn save-action${r.saved ? ' active' : ''}`}
              onClick={() => onToggleLike(r.id)}
            >
              <Heart
                size={20}
                strokeWidth={1.75}
                fill={r.saved ? 'currentColor' : 'none'}
              />
              <span>{r.saved ? 'Saved' : 'Like'}</span>
            </button>
            <button
              type="button"
              className={`meals-action-btn cook-action${r.cooked ? ' active' : ''}`}
              onClick={() => onToggleCooked(r.id)}
            >
              <ChefHat
                size={20}
                strokeWidth={1.75}
                fill={r.cooked ? 'currentColor' : 'none'}
              />
              <span>{r.cooked ? 'Cooked' : 'Mark cooked'}</span>
            </button>
            {onAddToList && (
              <button
                type="button"
                className={`meals-action-btn list-action${gs.listStatus === 'done' ? ' active' : ''}`}
                disabled={gs.listStatus === 'loading' || gs.listStatus === 'done'}
                onClick={async () => {
                  setListStatus('loading')
                  try {
                    await onAddToList(r.id, r.ingredients)
                    setListStatus('done')
                    setAddedIngredients(() => new Set(r.ingredients.map((_, i) => i)))
                  } catch {
                    setListStatus('idle')
                  }
                }}
              >
                {gs.listStatus === 'done'
                  ? <Check size={20} strokeWidth={1.75} />
                  : <ShoppingCart size={20} strokeWidth={1.75} />}
                <span>{gs.listStatus === 'done' ? 'On the list' : gs.listStatus === 'loading' ? 'Adding…' : 'Add to list'}</span>
              </button>
            )}
            <button
              type="button"
              className="meals-action-btn"
            >
              <Share2 size={20} strokeWidth={1.75} />
              <span>Share</span>
            </button>
          </div>

          {/* Your rating */}
          <div className="meals-detail-section">
              <div className="meals-detail-section-head">
                <h2 className="meals-detail-section-title">Your rating</h2>
              </div>
              <StarInput
                value={r.myRating || 0}
                onChange={v => onRate(r.id, v)}
              />
            </div>

          {/* Ingredients */}
          {r.ingredients.length > 0 && (
            <div className="meals-detail-section">
              <div className="meals-detail-section-head">
                <h2 className="meals-detail-section-title">Ingredients</h2>
                <span style={{ color: 'var(--m-fg-3)', fontSize: 12 }}>
                  {r.ingredients.length} items
                </span>
              </div>
              <ul className="meals-ingredients">
                {r.ingredients.map((ing, i) => (
                  <li key={i}>
                    {ing.qty && (
                      <span className="meals-ingredient-qty">{ing.qty}</span>
                    )}
                    <span className="meals-ingredient-name">{ing.name}</span>
                    {onAddToList && (
                      <button
                        type="button"
                        className={`meals-ingredient-add${gs.addedIngredients.has(i) ? ' added' : ''}`}
                        aria-label={`Add ${ing.name} to grocery list`}
                        onClick={async () => {
                          if (gs.addedIngredients.has(i)) return
                          try {
                            await onAddToList(r.id, [ing])
                            setAddedIngredients(prev => new Set(prev).add(i))
                          } catch { /* silent */ }
                        }}
                      >
                        {gs.addedIngredients.has(i)
                          ? <Check size={14} strokeWidth={2} />
                          : <Plus size={14} strokeWidth={2} />}
                      </button>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Instructions */}
          {r.steps.length > 0 && (
            <div className="meals-detail-section">
              <div className="meals-detail-section-head">
                <h2 className="meals-detail-section-title">Instructions</h2>
              </div>
              <ul className="meals-steps">
                {r.steps.map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Source */}
          {r.source?.url && (
            <div className="meals-detail-section">
              <div className="meals-detail-section-head">
                <h2 className="meals-detail-section-title">Source</h2>
              </div>
              <a
                className="meals-source-link"
                href={r.source.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                <ExternalLink size={14} strokeWidth={1.75} />
                <span>{r.source.name}</span>
                {r.source.domain && (
                  <span className="meals-source-domain">· {r.source.domain}</span>
                )}
              </a>
            </div>
          )}

          {/* Last cooked */}
          {lastCookedLabel && (
            <div
              style={{
                color: 'var(--m-fg-3)',
                fontSize: 12.5,
                textAlign: 'center',
                paddingTop: 8,
              }}
            >
              Last cooked {lastCookedLabel}
            </div>
          )}
        </div>
      </aside>
    </>
  )
}
