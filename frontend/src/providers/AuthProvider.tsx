import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import { AuthContext, type AuthContextValue } from '@/hooks/useAuth'

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [authState, setAuthState] = useState<Pick<AuthContextValue, 'user' | 'session' | 'loading'>>({
    user: null,
    session: null,
    loading: true,
  })

  useEffect(() => {
    let cancelled = false
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!cancelled) {
        setAuthState({
          user: session?.user ?? null,
          session,
          loading: false,
        })
      }
    })

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, session) => {
        setAuthState({
          user: session?.user ?? null,
          session,
          loading: false,
        })
      }
    )

    return () => {
      cancelled = true
      subscription.unsubscribe()
    }
  }, [])

  const signInWithGoogle = async () => {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: window.location.origin }
    })
  }

  const signOut = async () => {
    await supabase.auth.signOut()
  }

  return (
    <AuthContext value={{ ...authState, signInWithGoogle, signOut }}>
      {children}
    </AuthContext>
  )
}
