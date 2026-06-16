import { Link } from 'react-router-dom'
import { useHousehold } from '@/hooks/useHousehold'
import { useProfile } from '@/hooks/useProfile'
import { AppShell } from '@/components/layout/AppShell'
import { SECTIONS } from '@/config/sections'

export default function HomePage() {
  const { household } = useHousehold()
  const profile = useProfile()

  return (
    <AppShell profile={profile}>
      <div className="max-w-2xl mx-auto px-6 py-10 flex flex-col gap-8">
        <div>
          <h1 className="text-2xl font-semibold">
            Welcome{household ? `, ${household.name}` : ''}
          </h1>
          <p className="text-muted-foreground mt-1">Pick where you want to go</p>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {SECTIONS.map(section => (
            <SectionCard key={section.id} section={section} />
          ))}
        </div>
      </div>
    </AppShell>
  )
}

function SectionCard({ section }: { section: typeof SECTIONS[number] }) {
  const card = (
    <div
      className="rounded-xl p-6 flex flex-col gap-2 transition-colors"
      style={{
        border: `2px solid ${section.color}`,
        background: 'hsl(var(--card))',
        opacity: section.disabled ? 0.5 : 1,
      }}
    >
      <span className="text-3xl">{section.icon}</span>
      <h2 className="text-base font-semibold" style={{ color: section.color }}>
        {section.title}
      </h2>
      <p className="text-sm text-muted-foreground">{section.description}</p>
      {section.disabled && (
        <span className="text-xs text-muted-foreground mt-1">Coming soon</span>
      )}
    </div>
  )

  if (section.disabled) return card

  return (
    <Link to={`/${section.id}`} className="hover:opacity-90 active:scale-[0.98] transition-all">
      {card}
    </Link>
  )
}
