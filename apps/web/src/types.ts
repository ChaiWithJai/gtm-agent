export interface Message {
  role: 'user' | 'assistant'
  content: string
  options?: string[]
  question_id?: string
}

export interface Scorecard {
  level: number
  scores: Record<string, number>
  gaps: string[]
  recommendations: string[]
}

export interface SessionState {
  thread_id: string
  messages: Message[]
  diagnostic_complete: boolean
  current_question: number
  scorecard: Scorecard | null
  artifacts: string[]
}

export interface StartResponse {
  thread_id: string
  messages: Message[]
}

export interface SSEEvent {
  event: string
  content?: string
  options?: string[]
  scorecard?: Scorecard
  filename?: string
}
