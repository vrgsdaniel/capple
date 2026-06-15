import api from '@/lib/api'
import type { Ingredient } from '@/types/groceries'

export function useAddToGroceries() {
  const addFromRecipe = async (recipeId: string, ingredients: Ingredient[]) => {
    await api.post('/api/grocery-items/from-recipe', { recipe_id: recipeId, ingredients })
  }

  return { addFromRecipe }
}
