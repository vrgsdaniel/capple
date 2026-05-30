import { useState } from 'react'
import { Clock, Heart } from 'lucide-react'
import { StarDisplay } from './StarRating'
import type { Recipe } from '@/types/meals'

interface ThumbProps {
  recipe: Recipe
}

function Thumb({ recipe }: ThumbProps) {
  const [errored, setErrored] = useState(false)

  if (errored || !recipe.image) {
    return (
      <div className="meals-thumb-fallback">
        <span style={{ fontSize: 40 }}>{recipe.emoji}</span>
      </div>
    )
  }

  return (
    <img
      src={recipe.image}
      alt=""
      loading="lazy"
      onError={() => setErrored(true)}
    />
  )
}

interface Props {
  recipe: Recipe
  onOpen: (id: string) => void
  onToggleLike: (id: string) => void
}

export default function RecipeCard({ recipe, onOpen, onToggleLike }: Props) {
  return (
    <div className="meals-card" onClick={() => onOpen(recipe.id)}>
      <div className="meals-card-thumb">
        <Thumb recipe={recipe} />
        <div className="meals-card-overlay" onClick={e => e.stopPropagation()}>
          <button
            type="button"
            className={`meals-icon-btn${recipe.saved ? ' saved' : ''}`}
            onClick={() => onToggleLike(recipe.id)}
            title={recipe.saved ? 'Liked' : 'Like'}
          >
            <Heart
              size={15}
              strokeWidth={1.75}
              fill={recipe.saved ? 'currentColor' : 'none'}
            />
          </button>
        </div>
      </div>
      <div className="meals-card-body">
        <div className="meals-card-title">{recipe.title}</div>
        <div className="meals-card-meta">
          <span className="meals-rating-display">
            <StarDisplay rating={recipe.rating} size={11} />
            <span className="meals-rating-value">{recipe.rating.toFixed(1)}</span>
          </span>
          <span className="meals-meta-dot">·</span>
          <span className="meals-meta-time">
            <Clock size={11} strokeWidth={1.75} />
            {recipe.time}m
          </span>
        </div>
        <div className="meals-card-pills">
          <span className="meals-pill">{recipe.mealType}</span>
          <span className="meals-pill">{recipe.difficulty}</span>
        </div>
      </div>
    </div>
  )
}
