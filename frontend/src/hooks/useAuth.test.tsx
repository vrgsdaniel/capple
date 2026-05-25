import { renderHook } from '@testing-library/react'
import type { ReactNode } from 'react'
import type { Session, User } from '@supabase/supabase-js'
import { AuthContext, useAuth } from '@/hooks/useAuth'

describe('useAuth', () => {
  it('throws when used outside AuthProvider', () => {
    expect(() => renderHook(() => useAuth())).toThrow('useAuth must be used within AuthProvider')
  })

  it('returns context value when used inside AuthProvider', () => {
    const value = {
      user: { id: 'user-1' } as User,
      session: { access_token: 'token-1' } as Session,
      loading: false,
      signInWithGoogle: jest.fn(async () => undefined),
      signOut: jest.fn(async () => undefined),
    }

    function Wrapper({ children }: { children: ReactNode }) {
      return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
    }

    const { result } = renderHook(() => useAuth(), { wrapper: Wrapper })

    expect(result.current).toBe(value)
  })
})
