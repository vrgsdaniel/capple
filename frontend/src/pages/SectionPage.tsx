import { useParams, Navigate } from 'react-router-dom'
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
    <AppShell backTo="/" profile={profile}>
      <div className="max-w-3xl mx-auto px-4 py-6">
        {section.render({ profile, household })}
      </div>
      <ChatDrawer />
    </AppShell>
  )
}
