import { useEffect, useState } from 'react'
import { X, Clock, Users, Star, Heart, ChefHat, Share2, ExternalLink } from 'lucide-react'
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
  onUpdate: (id: string, patch: Partial<Recipe>) => void
}

export default function RecipeSheet({ recipe, open, onClose, onUpdate }: Props) {
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    if (open) window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!recipe) return null
  const r = recipe

  function handleLogCook() {
    onUpdate(r.id, {
      cooked: true,
      cookedCount: (r.cookedCount || 0) + 1,
      lastCooked: new Date().toISOString().slice(0, 10),
    })
  }

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
              onClick={() => onUpdate(r.id, { saved: !r.saved })}
            >
              <Heart
                size={20}
                strokeWidth={1.75}
                fill={r.saved ? 'currentColor' : 'none'}
              />
              <span>{r.saved ? 'Loved' : 'Save'}</span>
            </button>
            <button
              type="button"
              className={`meals-action-btn cook-action${r.cooked ? ' active' : ''}`}
              onClick={handleLogCook}
            >
              <ChefHat
                size={20}
                strokeWidth={1.75}
                fill={r.cooked ? 'currentColor' : 'none'}
              />
              <span>{r.cooked ? 'Cooked' : 'Mark cooked'}</span>
            </button>
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
              {r.myRating > 0 && (
                <button
                  type="button"
                  className="meals-btn ghost"
                  style={{ padding: '4px 8px', fontSize: 12, color: 'var(--m-fg-3)' }}
                  onClick={() => onUpdate(r.id, { myRating: 0 })}
                >
                  Clear
                </button>
              )}
            </div>
            <StarInput
              value={r.myRating || 0}
              onChange={v => onUpdate(r.id, { myRating: v })}
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
