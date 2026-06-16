import { useEffect, useRef, useState } from 'react'
import { useRegisterSW } from 'virtual:pwa-register/react'

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

const DISMISSED_KEY = 'pwa-install-dismissed'

export function PwaInstallPrompt() {
  const deferredPrompt = useRef<BeforeInstallPromptEvent | null>(null)
  const [show, setShow] = useState(false)

  // Keep SW updated in the background
  useRegisterSW({ immediate: true })

  useEffect(() => {
    // Only show on touch devices (mobile/tablet)
    if (!window.matchMedia('(pointer: coarse)').matches) return
    if (localStorage.getItem(DISMISSED_KEY)) return
    // Already installed as standalone
    if (window.matchMedia('(display-mode: standalone)').matches) return

    const handler = (e: Event) => {
      e.preventDefault()
      deferredPrompt.current = e as BeforeInstallPromptEvent
      setShow(true)
    }

    window.addEventListener('beforeinstallprompt', handler)
    return () => window.removeEventListener('beforeinstallprompt', handler)
  }, [])

  if (!show) return null

  async function handleInstall() {
    await deferredPrompt.current?.prompt()
    const { outcome } = await deferredPrompt.current!.userChoice
    if (outcome === 'dismissed') localStorage.setItem(DISMISSED_KEY, '1')
    setShow(false)
  }

  function handleDismiss() {
    localStorage.setItem(DISMISSED_KEY, '1')
    setShow(false)
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 flex items-center justify-between rounded-xl border bg-background px-4 py-3 shadow-lg sm:hidden">
      <p className="text-sm font-medium">Add Capple to your home screen</p>
      <div className="flex gap-2">
        <button
          onClick={handleDismiss}
          className="text-sm text-muted-foreground"
        >
          Not now
        </button>
        <button
          onClick={handleInstall}
          className="rounded-md bg-primary px-3 py-1 text-sm font-medium text-primary-foreground"
        >
          Install
        </button>
      </div>
    </div>
  )
}
