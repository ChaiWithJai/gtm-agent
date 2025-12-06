interface ArtifactListProps {
  artifacts: string[]
  onDownload: (filename: string) => void
}

const ARTIFACT_ICONS: Record<string, string> = {
  'gtm-scorecard.json': '📊',
  'gtm-narrative.md': '📝',
  'cold-email-sequence.md': '📧',
  'linkedin-posts.md': '💼',
  'action-plan.md': '✅',
}

const ARTIFACT_NAMES: Record<string, string> = {
  'gtm-scorecard.json': 'GTM Scorecard',
  'gtm-narrative.md': 'Strategic Narrative',
  'cold-email-sequence.md': 'Cold Email Sequence',
  'linkedin-posts.md': 'LinkedIn Posts',
  'action-plan.md': 'Action Plan',
}

export function ArtifactList({ artifacts, onDownload }: ArtifactListProps) {
  if (artifacts.length === 0) return null

  return (
    <div className="artifacts-section">
      <h3>Generated Artifacts</h3>
      {artifacts.map(filename => (
        <div key={filename} className="artifact-card">
          <div className="artifact-name">
            <span>{ARTIFACT_ICONS[filename] || '📄'}</span>
            <span>{ARTIFACT_NAMES[filename] || filename}</span>
          </div>
          <button
            className="download-btn"
            onClick={() => onDownload(filename)}
          >
            Download
          </button>
        </div>
      ))}
    </div>
  )
}
