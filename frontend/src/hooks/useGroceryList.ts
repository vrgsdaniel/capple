import { useState, useEffect, useCallback } from 'react'
import api from '@/lib/api'
import type { GroceryItem, GroceryList, Ingredient } from '@/types/groceries'

const EMPTY_LIST: GroceryList = { active: [], history: [] }

export function useGroceryList() {
  const [list, setList] = useState<GroceryList>(EMPTY_LIST)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchList = useCallback(async () => {
    try {
      const res = await api.get<GroceryList>('/api/grocery-items')
      setList(res.data)
      setError(null)
    } catch {
      setError('Could not load grocery list.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      try {
        const res = await api.get<GroceryList>('/api/grocery-items')
        if (!cancelled) { setList(res.data); setError(null) }
      } catch {
        if (!cancelled) setError('Could not load grocery list.')
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    run()
    return () => { cancelled = true }
  }, [])

  const addItem = async (name: string, qty: string | null) => {
    await api.post<GroceryItem>('/api/grocery-items', { name, qty: qty || null })
    await fetchList()
  }

  const markBought = async (itemId: string) => {
    // optimistic: remove from active immediately so the animation completes before refetch
    setList(prev => ({ ...prev, active: prev.active.filter(i => i.id !== itemId) }))
    try {
      await api.patch(`/api/grocery-items/${itemId}`, { bought: true })
      await fetchList()
    } catch {
      await fetchList() // revert
    }
  }

  const restoreItem = async (itemId: string) => {
    await api.patch(`/api/grocery-items/${itemId}`, { bought: false })
    await fetchList()
  }

  const removeItem = async (itemId: string) => {
    // optimistic: remove immediately
    setList(prev => ({
      ...prev,
      active: prev.active.filter(i => i.id !== itemId),
      history: prev.history.filter(i => i.id !== itemId),
    }))
    try {
      await api.delete(`/api/grocery-items/${itemId}`)
    } catch {
      await fetchList() // revert
    }
  }

  const clearHistory = async () => {
    await api.delete('/api/grocery-items/history')
    await fetchList()
  }

  const addFromRecipe = async (recipeId: string, ingredients: Ingredient[]) => {
    await api.post('/api/grocery-items/from-recipe', {
      recipe_id: recipeId,
      ingredients,
    })
    await fetchList()
  }

  return {
    list,
    loading,
    error,
    refetch: fetchList,
    addItem,
    markBought,
    restoreItem,
    removeItem,
    clearHistory,
    addFromRecipe,
  }
}
