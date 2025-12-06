# GTM Diagnostic Questions

The GTM Deep Agent uses three structured diagnostic questions based on the GTM Escalator framework to assess a founder's go-to-market maturity level.

## Question Flow

### Question 1: ICP Clarity (Phase: `icp`)

**Question ID:** `q1_icp`

**Question:** Who is your ideal customer?

**Options:**
1. SMB Founders (1-50 employees)
2. Mid-market (50-500 employees)
3. Enterprise (500+ employees)
4. Not sure yet

**Purpose:** Establishes the target market segment and validates ICP definition clarity.

### Question 2: Problem-Solution Fit (Phase: `messaging`)

**Question ID:** `q2_problem`

**Question:** How well can you describe the problem you solve?

**Options:**
1. Crystal clear - customers describe it to us
2. We know it, but articulation varies
3. Still figuring it out

**Purpose:** Assesses messaging clarity and problem-solution fit maturity.

### Question 3: Validation Level (Phase: `validation`)

**Question ID:** `q3_validation`

**Question:** What validation do you have?

**Options:**
1. Revenue from target ICP
2. Pilots/design partners
3. Customer interviews only
4. Not validated yet

**Purpose:** Determines the depth of market validation and evidence of product-market fit.

## Scoring Algorithm

Each answer contributes to the overall GTM level calculation:

### Level Scoring

| Answer | Score |
|--------|-------|
| Best option (first) | 3 |
| Good option (second) | 2 |
| Fair option (third) | 1 |
| Lowest option (fourth/last) | 0 |

### Level Thresholds

| Total Score | GTM Level | Description |
|-------------|-----------|-------------|
| 7-9 | Level 5 | GTM Excellence |
| 5-6 | Level 4 | Growth Ready |
| 3-4 | Level 3 | Good Foundation |
| 1-2 | Level 2 | Early Stage |
| 0 | Level 1 | Discovery |

## Output: Escalator Scorecard

After completing all three questions, the agent generates an Escalator Scorecard containing:

```json
{
  "level": 3,
  "scores": {
    "l1": 100,
    "l2": 100,
    "l3": 80,
    "l4": 40,
    "l5": 20
  },
  "gaps": [
    "Channel strategy undefined",
    "Sales playbook missing"
  ],
  "recommendations": [
    "Define 2-3 initial channels",
    "Document sales process"
  ]
}
```

## Integration Points

### Tool: `get_diagnostic_question`

```python
result = get_diagnostic_question.invoke({"question_number": 1})
# Returns:
# {
#   "question_id": "q1_icp",
#   "question_text": "Who is your ideal customer?",
#   "options": ["SMB Founders...", ...],
#   "phase": "icp"
# }
```

### Tool: `calculate_escalator_level`

```python
result = calculate_escalator_level.invoke({
    "answers": {
        "q1_icp": "SMB Founders (1-50 employees)",
        "q2_problem": "Crystal clear - customers describe it to us",
        "q3_validation": "Pilots/design partners"
    }
})
# Returns EscalatorScorecard
```

## UI Implementation

The frontend presents questions as button options:

1. Display question text
2. Show options as clickable buttons
3. Record selected option
4. Progress to next question
5. Display scorecard after completion

See `apps/web/src/components/OptionButtons.tsx` for implementation.
