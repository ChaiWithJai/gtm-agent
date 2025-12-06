import { ChatMessage, OptionButtons, Scorecard, ArtifactList, StartScreen } from './components'
import { useGTMAgent } from './hooks/useGTMAgent'

function App() {
  const {
    threadId,
    messages,
    isLoading,
    scorecard,
    artifacts,
    currentOptions,
    startSession,
    sendMessage,
    downloadArtifact,
  } = useGTMAgent()

  const handleOptionSelect = (option: string) => {
    sendMessage(option, option)
  }

  if (!threadId) {
    return (
      <div className="container">
        <div className="header">
          <h1>GTM Deep Agent</h1>
          <p>Transform scattered thinking into actionable GTM artifacts</p>
        </div>
        <div className="card">
          <StartScreen onStart={startSession} isLoading={isLoading} />
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="header">
        <h1>GTM Deep Agent</h1>
        <p>Transform scattered thinking into actionable GTM artifacts</p>
      </div>

      <div className="card">
        <div className="chat-container">
          {messages.map((message, index) => (
            <ChatMessage key={index} message={message} />
          ))}
        </div>

        {isLoading && (
          <div className="status-indicator">
            <div className="spinner" />
            <span>Thinking...</span>
          </div>
        )}

        <OptionButtons
          options={currentOptions}
          onSelect={handleOptionSelect}
          disabled={isLoading}
        />

        {scorecard && <Scorecard scorecard={scorecard} />}

        <ArtifactList artifacts={artifacts} onDownload={downloadArtifact} />
      </div>
    </div>
  )
}

export default App
