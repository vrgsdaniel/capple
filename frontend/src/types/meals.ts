export interface Recipe {
  id: string
  title: string
  emoji: string
  image: string
  mealType: 'breakfast' | 'lunch' | 'dinner' | 'snack'
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

export type SortKey = 'relevance' | 'fastest' | 'highest_rated' | 'name'

export interface RecipeSearchSpec {
  text: string
  mealTypes: Recipe['mealType'][]
  labels: string[]
  ingredients: string[]
  maxTotalMinutes: number | null
  liked: boolean | null
  cooked: boolean | null
  sort: SortKey
  page: number
  limit: number
}

export interface MealTypeOption {
  value: Recipe['mealType']
  label: string
  emoji: string
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

export const TIME_BUCKETS: TimeBucketOption[] = [
  { value: 15, label: '≤ 15 min' },
  { value: 30, label: '≤ 30 min' },
  { value: 60, label: '≤ 60 min' },
]

export const SORT_OPTIONS: SortOption[] = [
  { value: 'relevance', label: 'Best match' },
  { value: 'fastest', label: 'Fastest' },
  { value: 'highest_rated', label: 'Highest rated' },
  { value: 'name', label: 'Name' },
]
