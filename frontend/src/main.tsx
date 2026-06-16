import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useHousehold } from '@/hooks/useHousehold'
import { AuthProvider } from '@/providers/AuthProvider'
import { HouseholdProvider } from '@/providers/HouseholdProvider'
import { ThemeProvider } from '@/providers/ThemeProvider'
import { PwaInstallPrompt } from '@/components/common/PwaInstallPrompt'
import { OfflineBanner } from '@/components/common/OfflineBanner'
import './index.css'

const Login = lazy(() => import('@/pages/Login'))
const Onboarding = lazy(() => import('@/pages/Onboarding'))
const HomePage = lazy(() => import('@/pages/HomePage'))
const SectionPage = lazy(() => import('@/pages/SectionPage'))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return null
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

function HouseholdRoute({ children }: { children: React.ReactNode }) {
  const { household, loading } = useHousehold()
  if (loading) return null
  if (!household) return <Navigate to="/onboarding" replace />
  return <>{children}</>
}

function AppRoutes() {
  const { user, loading } = useAuth()
  if (loading) return null

  return (
    <Suspense fallback={null}>
      <Routes>
        <Route
          path="/login"
          element={user ? <Navigate to="/" replace /> : <Login />}
        />
        <Route
          path="/onboarding"
          element={
            <ProtectedRoute>
              <Onboarding />
            </ProtectedRoute>
          }
        />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <HouseholdRoute>
                <HomePage />
              </HouseholdRoute>
            </ProtectedRoute>
          }
        />
        <Route
          path="/:sectionId"
          element={
            <ProtectedRoute>
              <HouseholdRoute>
                <SectionPage />
              </HouseholdRoute>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Suspense>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
    <AuthProvider>
      <HouseholdProvider>
        <BrowserRouter>
          <OfflineBanner />
          <AppRoutes />
          <PwaInstallPrompt />
        </BrowserRouter>
      </HouseholdProvider>
    </AuthProvider>
    </ThemeProvider>
  </StrictMode>
)