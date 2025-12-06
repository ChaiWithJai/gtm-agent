import { useState } from 'react'

interface StartScreenProps {
  onStart: (productUrl?: string, productDescription?: string) => void
  isLoading: boolean
}

export function StartScreen({ onStart, isLoading }: StartScreenProps) {
  const [mode, setMode] = useState<'choice' | 'url' | 'describe' | null>(null)
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (mode === 'url') {
      onStart(input, undefined)
    } else {
      onStart(undefined, input)
    }
  }

  if (mode === null) {
    return (
      <div className="start-screen">
        <h2>Welcome to GTM Deep Agent</h2>
        <p>Transform your scattered GTM thinking into concrete, actionable artifacts.</p>

        <div className="start-options">
          <div className="start-option" onClick={() => setMode('url')}>
            <h3>Share a Product URL</h3>
            <p>I'll analyze your website to understand your product</p>
          </div>
          <div className="start-option" onClick={() => setMode('describe')}>
            <h3>Describe Your Product</h3>
            <p>Tell me about what you're building</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="start-screen">
      <h2>{mode === 'url' ? 'Enter Your Product URL' : 'Describe Your Product'}</h2>

      <form onSubmit={handleSubmit} className="input-form" style={{ maxWidth: '500px', margin: '2rem auto' }}>
        <input
          type={mode === 'url' ? 'url' : 'text'}
          className="input-field"
          placeholder={mode === 'url' ? 'https://yourproduct.com' : 'We build AI tools for...'}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isLoading}
          autoFocus
        />
        <button type="submit" className="submit-btn" disabled={isLoading || !input.trim()}>
          {isLoading ? 'Starting...' : 'Start'}
        </button>
      </form>

      <button
        onClick={() => setMode(null)}
        style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
      >
        ← Back
      </button>
    </div>
  )
}
