export interface GroceryItem {
  id: string
  household_id: string
  name: string
  qty: string | null
  bought: boolean
  bought_at: string | null
  source_recipe_title: string | null
  added_by: string | null
  created_at: string
  updated_at: string
}

export interface GroceryList {
  active: GroceryItem[]
  history: GroceryItem[]
}

export interface Ingredient {
  name: string
  qty?: string | null
}
