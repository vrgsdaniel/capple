import { useEffect } from 'react'
import { supabase } from '@/lib/supabase'

export function useBatteryRealtime(householdId: string, onUpdate: () => void) {
  useEffect(() => {
    if (!householdId) return

    const channel = supabase
      .channel(`battery-${householdId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'battery_logs',
          filter: `household_id=eq.${householdId}`,
        },
        () => onUpdate()
      )
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [householdId, onUpdate])
}