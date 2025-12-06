interface OptionButtonsProps {
  options: string[]
  onSelect: (option: string) => void
  disabled?: boolean
}

export function OptionButtons({ options, onSelect, disabled }: OptionButtonsProps) {
  if (options.length === 0) return null

  return (
    <div className="options-grid">
      {options.map((option, index) => (
        <button
          key={index}
          className="option-btn"
          onClick={() => onSelect(option)}
          disabled={disabled}
        >
          {option}
        </button>
      ))}
    </div>
  )
}
