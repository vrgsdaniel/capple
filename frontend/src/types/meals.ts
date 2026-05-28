export interface Recipe {
  id: string
  title: string
  emoji: string
  image: string
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  difficulty: 'easy' | 'medium' | 'hard'
  time: number
  rating: number
  myRating: number
  saved: boolean
  cooked: boolean
  cookedCount: number
  lastCooked: string | null
  servings: number
  description: string
  ingredients: { qty: string; name: string }[]
  steps: string[]
  source: { name: string | null; url: string | null; domain: string | null }
  tags: string[]
}

export type SortKey = 'default' | 'fastest' | 'rating' | 'cooked' | 'recent'

export interface MealTypeOption {
  value: string
  label: string
  emoji: string
}

export interface DifficultyOption {
  value: string
  label: string
}

export interface TimeBucketOption {
  value: number
  label: string
}

export interface SortOption {
  value: SortKey
  label: string
}

export const MEAL_TYPES: MealTypeOption[] = [
  { value: 'breakfast', label: 'Breakfast', emoji: '🥐' },
  { value: 'lunch', label: 'Lunch', emoji: '🥗' },
  { value: 'dinner', label: 'Dinner', emoji: '🍽️' },
  { value: 'snack', label: 'Snack', emoji: '🍪' },
]

export const DIFFICULTIES: DifficultyOption[] = [
  { value: 'easy', label: 'Easy' },
  { value: 'medium', label: 'Medium' },
  { value: 'hard', label: 'Hard' },
]

export const TIME_BUCKETS: TimeBucketOption[] = [
  { value: 15, label: '≤ 15 min' },
  { value: 30, label: '≤ 30 min' },
  { value: 60, label: '≤ 60 min' },
]

export const SORT_OPTIONS: SortOption[] = [
  { value: 'default', label: 'Recommended' },
  { value: 'fastest', label: 'Fastest' },
  { value: 'rating', label: 'Highest rated' },
  { value: 'cooked', label: 'Most cooked' },
  { value: 'recent', label: 'Recently cooked' },
]

export function fuzzyMatch(haystack: string, query: string): boolean {
  if (!query.trim()) return true
  const target = haystack.toLowerCase()
  const tokens = query.toLowerCase().trim().split(/\s+/)
  return tokens.every(tok => {
    if (target.includes(tok)) return true
    let i = 0
    for (const ch of target) {
      if (ch === tok[i]) i++
      if (i === tok.length) return true
    }
    return false
  })
}
