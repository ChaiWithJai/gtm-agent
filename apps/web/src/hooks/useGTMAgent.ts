import { useState, useCallback } from 'react'
import type { Message, Scorecard, SSEEvent } from '../types'

interface UseGTMAgentReturn {
  threadId: string | null
  messages: Message[]
  isLoading: boolean
  scorecard: Scorecard | null
  artifacts: string[]
  currentOptions: string[]
  startSession: (productUrl?: string, productDescription?: string) => Promise<void>
  sendMessage: (message: string, selectedOption?: string) => Promise<void>
  downloadArtifact: (filename: string) => void
}

export function useGTMAgent(): UseGTMAgentReturn {
  const [threadId, setThreadId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [scorecard, setScorecard] = useState<Scorecard | null>(null)
  const [artifacts, setArtifacts] = useState<string[]>([])
  const [currentOptions, setCurrentOptions] = useState<string[]>([])

  const startSession = useCallback(async (productUrl?: string, productDescription?: string) => {
    setIsLoading(true)
    try {
      const response = await fetch('/api/agent/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          product_url: productUrl,
          product_description: productDescription,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to start session')
      }

      const data = await response.json()
      setThreadId(data.thread_id)
      setMessages(data.messages)

      // Extract options from the last message
      const lastMsg = data.messages[data.messages.length - 1]
      if (lastMsg?.options) {
        setCurrentOptions(lastMsg.options)
      }
    } catch (error) {
      console.error('Error starting session:', error)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const sendMessage = useCallback(async (message: string, selectedOption?: string) => {
    if (!threadId) return

    setIsLoading(true)
    setCurrentOptions([])

    try {
      const response = await fetch('/api/agent/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          thread_id: threadId,
          message,
          selected_option: selectedOption,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      // Handle SSE stream
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) return

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const text = decoder.decode(value)
        const lines = text.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const eventData: SSEEvent = JSON.parse(line.slice(6))

            switch (eventData.event) {
              case 'user_message':
                setMessages(prev => [...prev, { role: 'user', content: eventData.content! }])
                break
              case 'message':
                setMessages(prev => [...prev, { role: 'assistant', content: eventData.content! }])
                break
              case 'options':
                setCurrentOptions(eventData.options || [])
                break
              case 'scorecard':
                setScorecard(eventData.scorecard || null)
                break
              case 'artifact':
                setArtifacts(prev => [...prev, eventData.filename!])
                break
              case 'done':
                break
            }
          }
        }
      }
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setIsLoading(false)
    }
  }, [threadId])

  const downloadArtifact = useCallback((filename: string) => {
    if (!threadId) return
    window.open(`/api/artifacts/${threadId}/${filename}`, '_blank')
  }, [threadId])

  return {
    threadId,
    messages,
    isLoading,
    scorecard,
    artifacts,
    currentOptions,
    startSession,
    sendMessage,
    downloadArtifact,
  }
}
