import type { Scorecard as ScorecardType } from '../types'

interface ScorecardProps {
  scorecard: ScorecardType
}

export function Scorecard({ scorecard }: ScorecardProps) {
  return (
    <div className="scorecard">
      <h3>Your GTM Maturity</h3>
      <div className="scorecard-level">Level {scorecard.level}</div>

      <div className="level-progress">
        {[1, 2, 3, 4, 5].map(level => (
          <div
            key={level}
            className={`level-dot ${level <= scorecard.level ? 'active' : ''}`}
          />
        ))}
      </div>

      {scorecard.gaps.length > 0 && (
        <>
          <h4>Key Gaps to Address</h4>
          <ul className="gaps-list">
            {scorecard.gaps.map((gap, index) => (
              <li key={index}>{gap}</li>
            ))}
          </ul>
        </>
      )}

      {scorecard.recommendations.length > 0 && (
        <>
          <h4 style={{ marginTop: '1rem' }}>Recommendations</h4>
          <ul className="gaps-list">
            {scorecard.recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
