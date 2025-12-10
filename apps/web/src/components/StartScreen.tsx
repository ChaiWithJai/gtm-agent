import { useState } from 'react'

interface StartScreenProps {
  onStart: (productUrl?: string, productDescription?: string) => void
  isLoading: boolean
}

/**
 * Normalize a URL input - adds https:// if missing, handles various formats.
 * Accepts: example.com, www.example.com, https://example.com, etc.
 */
function normalizeUrl(input: string): string {
  let url = input.trim().toLowerCase()

  // Remove any leading/trailing whitespace and quotes
  url = url.replace(/^["'\s]+|["'\s]+$/g, '')

  // If it doesn't start with a protocol, add https://
  if (!url.startsWith('http://') && !url.startsWith('https://')) {
    url = `https://${url}`
  }

  return url
}

/**
 * Validate if the input looks like a valid URL.
 * More permissive than browser validation - accepts bare domains.
 */
function isValidUrlInput(input: string): { valid: boolean; error?: string } {
  const trimmed = input.trim()

  if (!trimmed) {
    return { valid: false, error: 'Please enter a URL' }
  }

  // Basic domain pattern: word.word (minimum)
  const domainPattern = /^(https?:\/\/)?[\w-]+(\.[\w-]+)+/i

  if (!domainPattern.test(trimmed)) {
    return { valid: false, error: 'Enter a domain like "company.com"' }
  }

  // Check for obviously invalid patterns
  if (trimmed.includes(' ')) {
    return { valid: false, error: 'URL cannot contain spaces' }
  }

  return { valid: true }
}

export function StartScreen({ onStart, isLoading }: StartScreenProps) {
  const [mode, setMode] = useState<'choice' | 'url' | 'describe' | null>(null)
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
    // Clear error when user starts typing
    if (error) setError(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()

    if (mode === 'url') {
      // Validate URL
      const validation = isValidUrlInput(input)
      if (!validation.valid) {
        setError(validation.error || 'Invalid URL')
        return
      }

      // Normalize and submit
      const normalizedUrl = normalizeUrl(input)
      onStart(normalizedUrl, undefined)
    } else {
      // Description mode - just check it's not empty
      if (!input.trim()) {
        setError('Please describe your product')
        return
      }
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

      <form onSubmit={handleSubmit} className="input-form" style={{ maxWidth: '500px', margin: '2rem auto', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', gap: '0.75rem', width: '100%' }}>
          <input
            type="text"
            className="input-field"
            placeholder={mode === 'url' ? 'company.com' : 'We build AI tools for...'}
            value={input}
            onChange={handleInputChange}
            disabled={isLoading}
            autoFocus
            style={error ? { borderColor: '#ef4444' } : {}}
          />
          <button type="submit" className="submit-btn" disabled={isLoading || !input.trim()}>
            {isLoading ? 'Analyzing...' : 'Start'}
          </button>
        </div>

        {error && (
          <p style={{ color: '#ef4444', fontSize: '0.875rem', margin: '0.25rem 0 0 0', textAlign: 'left' }}>
            {error}
          </p>
        )}

        {mode === 'url' && !error && (
          <p style={{ color: 'var(--text-muted)', fontSize: '0.875rem', margin: '0.25rem 0 0 0', textAlign: 'left' }}>
            Just enter the domain - no need for https:// or www.
          </p>
        )}
      </form>

      <button
        onClick={() => { setMode(null); setError(null); setInput(''); }}
        style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}
      >
        ← Back
      </button>
    </div>
  )
}
