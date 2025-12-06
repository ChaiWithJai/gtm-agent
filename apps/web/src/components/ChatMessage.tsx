import type { Message } from '../types'

interface ChatMessageProps {
  message: Message
}

export function ChatMessage({ message }: ChatMessageProps) {
  return (
    <div className={`message ${message.role}`}>
      <div className="message-content">
        {message.content}
      </div>
    </div>
  )
}
