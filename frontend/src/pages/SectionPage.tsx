import { useParams, Navigate, Link } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { SECTIONS } from '@/config/sections'
import { useProfile } from '@/hooks/useProfile'
import { useHousehold } from '@/hooks/useHousehold'
import ChatDrawer from '@/components/chat/ChatDrawer'

export default function SectionPage() {
  const { sectionId } = useParams<{ sectionId: string }>()
  const profile = useProfile()
  const { household } = useHousehold()

  const section = SECTIONS.find(s => s.id === sectionId)
  if (!section) return <Navigate to="/" replace />

  return (
    <AppShell profile={profile}>
      <div className="border-b border-border">
        <div className="max-w-3xl mx-auto px-4">
          <div className="flex gap-1 py-2 overflow-x-auto">
            {SECTIONS.filter(s => !s.disabled).map(s => (
              <Link
                key={s.id}
                to={`/${s.id}`}
                className="shrink-0 flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors"
                style={s.id === sectionId ? {
                  background: s.color + '22',
                  color: s.color,
                } : {
                  color: 'var(--muted-foreground)',
                }}
              >
                <span>{s.icon}</span>
                <span>{s.title}</span>
              </Link>
            ))}
          </div>
        </div>
      </div>
      <div className="max-w-3xl mx-auto px-4 py-6">
        {section.render({ profile, household })}
      </div>
      <ChatDrawer />
    </AppShell>
  )
}
