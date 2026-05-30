import { useState, useEffect, useRef } from 'react'
import api from '@/lib/api'
import type { Recipe } from '@/types/meals'

// ─── API response shapes ───────────────────────────────────────────────────

interface ApiListItem {
  id: string
  name: string
  recipe_type: string
  labels: string[]
  prep_time_minutes: number
  cook_time_minutes: number
  rating: number | null
  image_uri: string | null
  liked: boolean
  cooked: boolean
  user_rating: number | null
}

interface ApiDetail extends ApiListItem {
  ingredients: string[]
  instructions: string
  source_name: string | null
  source_url: string | null
  servings: number | null
  image_uri: string | null
}

// ─── Mapping helpers ───────────────────────────────────────────────────────

const VALID_MEAL_TYPES = new Set(['breakfast', 'lunch', 'dinner', 'snack'])

function normalizeMealType(type: string): Recipe['mealType'] {
  const lower = type.toLowerCase()
  return VALID_MEAL_TYPES.has(lower) ? (lower as Recipe['mealType']) : 'dinner'
}

function emojiForType(type: string): string {
  const map: Record<string, string> = {
    breakfast: '🥐',
    lunch: '🥗',
    dinner: '🍽️',
    snack: '🍪',
  }
  return map[type.toLowerCase()] ?? '🍽️'
}

function fromListItem(item: ApiListItem): Recipe {
  return {
    id: item.id,
    title: item.name,
    emoji: emojiForType(item.recipe_type),
    image: item.image_uri ?? '',
    mealType: normalizeMealType(item.recipe_type),
    difficulty: 'easy',
    time: (item.prep_time_minutes ?? 0) + (item.cook_time_minutes ?? 0),
    rating: item.rating ?? 0,
    myRating: item.user_rating ?? 0,
    saved: item.liked,
    cooked: item.cooked,
    cookedCount: 0,
    lastCooked: null,
    servings: 2,
    description: '',
    ingredients: [],
    steps: [],
    source: { name: null, url: null, domain: null },
    tags: item.labels ?? [],
  }
}

function detailPatch(detail: ApiDetail): Partial<Recipe> {
  const steps = detail.instructions
    ? detail.instructions.split(/\n+/).map(s => s.trim()).filter(Boolean)
    : []

  let domain: string | null = null
  if (detail.source_url) {
    try {
      domain = new URL(detail.source_url).hostname
    } catch {
      domain = null
    }
  }

  return {
    image: detail.image_uri ?? '',
    servings: detail.servings ?? 2,
    rating: detail.rating ?? 0,
    saved: detail.liked,
    cooked: detail.cooked,
    myRating: detail.user_rating ?? 0,
    ingredients: (detail.ingredients ?? []).map(ing => {
      if (typeof ing === 'string') return { qty: '', name: ing }
      const obj = ing as Record<string, string>
      return { qty: obj.amount ?? obj.qty ?? '', name: obj.item ?? obj.name ?? '' }
    }),
    steps,
    source: {
      name: detail.source_name ?? null,
      url: detail.source_url ?? null,
      domain,
    },
  }
}

// ─── Hook ──────────────────────────────────────────────────────────────────

export function useRecipes() {
  const [recipes, setRecipes] = useState<Recipe[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const fetchedDetails = useRef(new Set<string>())

  useEffect(() => {
    api
      .get<{ items: ApiListItem[] }>('/api/recipes', { params: { limit: 100 } })
      .then(res => setRecipes(res.data.items.map(fromListItem)))
      .catch(() => setError('Failed to load recipes'))
      .finally(() => setLoading(false))
  }, [])

  function updateRecipe(id: string, patch: Partial<Recipe>) {
    setRecipes(rs => rs.map(r => (r.id === id ? { ...r, ...patch } : r)))
  }

  async function ensureDetails(id: string): Promise<void> {
    if (fetchedDetails.current.has(id)) return
    fetchedDetails.current.add(id)
    try {
      const res = await api.get<ApiDetail>(`/api/recipes/${id}`)
      updateRecipe(id, detailPatch(res.data))
    } catch {
      fetchedDetails.current.delete(id)
    }
  }

  async function toggleLike(id: string): Promise<void> {
    const res = await api.post<ApiDetail>(`/api/recipes/${id}/like`)
    updateRecipe(id, { saved: res.data.liked })
  }

  async function toggleCooked(id: string): Promise<void> {
    const res = await api.post<ApiDetail>(`/api/recipes/${id}/cooked`)
    updateRecipe(id, { cooked: res.data.cooked })
  }

  async function rateRecipe(id: string, rating: number): Promise<void> {
    const res = await api.post<ApiDetail>(`/api/recipes/${id}/rate`, { rating })
    updateRecipe(id, { myRating: res.data.user_rating ?? 0, rating: res.data.rating ?? 0 })
  }

  return { recipes, loading, error, updateRecipe, ensureDetails, toggleLike, toggleCooked, rateRecipe }
}
