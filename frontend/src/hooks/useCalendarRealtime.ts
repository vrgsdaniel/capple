import { useEffect, useRef } from 'react'
import { supabase } from '@/lib/supabase'

export function useCalendarRealtime(householdId: string, onUpdate: () => void) {
  // Keep the channel alive across re-renders where `onUpdate`'s identity changes (e.g. month
  // navigation) — only householdId should tear down and re-open the subscription.
  const onUpdateRef = useRef(onUpdate)
  useEffect(() => {
    onUpdateRef.current = onUpdate
  })

  useEffect(() => {
    if (!householdId) return

    const channel = supabase
      .channel(`calendar-${householdId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'app',
          table: 'calendar_events',
          filter: `household_id=eq.${householdId}`,
        },
        () => onUpdateRef.current()
      )
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'app',
          table: 'calendar_birthdays',
          filter: `household_id=eq.${householdId}`,
        },
        () => onUpdateRef.current()
      )
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [householdId])
}
