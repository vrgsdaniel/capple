import { lazy, Suspense } from 'react'
import type { Profile } from '@/hooks/useProfile'
import type { Household } from '@/hooks/useHousehold'

const TasksTab = lazy(() => import('@/components/tasks/TasksTab'))
const BatteryTab = lazy(() => import('@/components/battery/BatteryTab'))
const MealsTab = lazy(() => import('@/components/meals/MealsTab'))
const GroceriesTab = lazy(() => import('@/components/groceries/GroceriesTab'))

export interface SectionContext {
  profile: Profile | null
  household: Household | null
}

export interface Section {
  id: string
  title: string
  icon: string
  color: string
  description: string
  disabled?: boolean
  render: (ctx: SectionContext) => React.ReactNode
}

// ─── Add new sections here — this is the only file you need to touch ──────────
export const SECTIONS: Section[] = [
  {
    id: 'tasks',
    title: 'Chores',
    icon: '🧽',
    color: '#A78BFA',
    description: 'Household chores & tasks',
    render: ({ profile, household }) =>
      profile && household ? (
        <Suspense fallback={null}>
          <TasksTab userId={profile.id} householdId={household.id} />
        </Suspense>
      ) : null,
  },
  {
    id: 'battery',
    title: 'Battery',
    icon: '⚡',
    color: '#9ACD32',
    description: 'Track your daily energy',
    render: ({ profile, household }) =>
      profile && household ? (
        <Suspense fallback={null}>
          <BatteryTab userId={profile.id} userName={profile.name} householdId={household.id} />
        </Suspense>
      ) : null,
  },
  {
    id: 'meals',
    title: 'Meals',
    icon: '🍽️',
    color: '#FF8C42',
    description: 'Browse & plan recipes',
    render: () => (
      <Suspense fallback={null}>
        <MealsTab />
      </Suspense>
    ),
  },
  {
    id: 'groceries',
    title: 'Groceries',
    icon: '🛒',
    color: '#4ECDC4',
    description: 'Manage your shopping list',
    render: ({ household }) =>
      household ? (
        <Suspense fallback={null}>
          <GroceriesTab householdId={household.id} />
        </Suspense>
      ) : null,
  },
  {
    id: 'activities',
    title: 'Activities',
    icon: '📅',
    color: '#FF6B9D',
    description: 'Log & analyze activities',
    disabled: true,
    render: () => (
      <p className="text-muted-foreground text-center mt-16">Coming soon</p>
    ),
  },
]
