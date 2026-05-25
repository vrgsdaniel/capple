import { render, screen, within } from '@testing-library/react'
import ChatMessages from '@/components/chat/ChatMessages'
import type { Message } from '@/types/chat'

describe('ChatMessages', () => {
  it('formats assistant content into paragraphs and list items', () => {
    const messages: Message[] = [
      {
        role: 'assistant',
        content:
          'Plan for tonight: - Keep it light and flexible - Pick 2-3 spots **Plan B:** Walk + one drink',
      },
    ]

    render(<ChatMessages messages={messages} streaming={false} error={null} />)

    expect(screen.getByText('Plan for tonight:')).toBeInTheDocument()

    const list = screen.getByRole('list')
    const items = within(list).getAllByRole('listitem')

    expect(items).toHaveLength(2)
    expect(items[0]).toHaveTextContent('Keep it light and flexible')
    expect(items[1]).toHaveTextContent('Pick 2-3 spots')
    expect(screen.getByText('Plan B:')).toBeInTheDocument()
    expect(screen.getByText('Walk + one drink')).toBeInTheDocument()
  })

  it('renders inline markdown-style bold segments for assistant responses', () => {
    const messages: Message[] = [
      {
        role: 'assistant',
        content: 'In Madrid tonight it is **mainly clear ~25C** with **low rain risk**.',
      },
    ]

    render(<ChatMessages messages={messages} streaming={false} error={null} />)

    const strongMainlyClear = screen.getByText('mainly clear ~25C')
    const strongLowRain = screen.getByText('low rain risk')

    expect(strongMainlyClear.tagName.toLowerCase()).toBe('strong')
    expect(strongLowRain.tagName.toLowerCase()).toBe('strong')
  })

  it('shows multiline user content as entered', () => {
    const messages: Message[] = [
      {
        role: 'user',
        content: 'Line one\nLine two',
      },
    ]

    render(<ChatMessages messages={messages} streaming={false} error={null} />)

    const text = screen.getByText(/Line one/)
    expect(text).toHaveClass('whitespace-pre-wrap')
    expect(text).toHaveTextContent('Line one')
    expect(text).toHaveTextContent('Line two')
  })
})
