import { useEffect } from 'react'
import { supabase } from '@/lib/supabase'

export function useTasksRealtime(householdId: string, onUpdate: () => void) {
  useEffect(() => {
    if (!householdId) return

    const channel = supabase
      .channel(`tasks-${householdId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'app',
          table: 'tasks',
          filter: `household_id=eq.${householdId}`,
        },
        () => onUpdate()
      )
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [householdId, onUpdate])
}
