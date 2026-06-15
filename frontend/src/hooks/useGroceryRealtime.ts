import { useEffect } from 'react'
import { supabase } from '@/lib/supabase'

export function useGroceryRealtime(householdId: string, onUpdate: () => void) {
  useEffect(() => {
    if (!householdId) return

    const channel = supabase
      .channel(`groceries-${householdId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'app',
          table: 'grocery_items',
          filter: `household_id=eq.${householdId}`,
        },
        () => onUpdate()
      )
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [householdId, onUpdate])
}
