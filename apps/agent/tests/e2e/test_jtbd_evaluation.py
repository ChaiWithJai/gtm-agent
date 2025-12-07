"""E2E tests with LLM-as-Judge evaluation against JTBD criteria.

Uses semantic evaluation to judge whether the GTM Agent workflow
successfully helps founders accomplish their Jobs-to-Be-Done.
"""

import json
import os
import time
from dataclasses import dataclass
from typing import Literal

import pytest
import requests
from anthropic import Anthropic

# JTBD Framework for GTM Agent
JTBD_CRITERIA = """
## Jobs-to-Be-Done: GTM Deep Agent

### Primary Job
"When I'm a founder with scattered GTM thinking, I want to get clear, actionable
GTM artifacts so I can confidently pitch investors and acquire customers."

### Functional Jobs (What they need to DO)
1. DIAGNOSE: Quickly assess where I am in my GTM journey (Level 1-5)
2. CLARIFY: Understand my gaps and what's blocking progress
3. PRODUCE: Generate concrete artifacts I can use immediately
4. PRIORITIZE: Know what to focus on next

### Emotional Jobs (How they want to FEEL)
1. CONFIDENT: Feel like I have a real strategy, not just ideas
2. VALIDATED: Know my level is based on real criteria, not guesswork
3. RELIEVED: Stop feeling overwhelmed by GTM complexity
4. EMPOWERED: Have tools to take action today

### Social Jobs (How they want to be PERCEIVED)
1. PREPARED: Look like I have my GTM act together to investors
2. STRATEGIC: Be seen as thoughtful about go-to-market
3. PROFESSIONAL: Have polished artifacts to share externally

### Success Criteria
- Diagnostic takes < 3 minutes
- Scorecard provides clear level with visual progress
- Gaps are specific and actionable (not generic advice)
- Recommendations map to next level requirements
- Artifacts are immediately usable (not templates needing heavy editing)
"""

JUDGE_SYSTEM_PROMPT = """You are an expert evaluator assessing AI agent workflows
against Jobs-to-Be-Done (JTBD) criteria. You provide objective, structured evaluations.

Your task is to judge whether an AI agent's responses successfully help users
accomplish their jobs-to-be-done. Be rigorous but fair.

Score each dimension from 1-5:
1 = Completely fails to address the job
2 = Partially addresses but major gaps
3 = Adequately addresses the job
4 = Well addresses with minor improvements possible
5 = Excellently addresses the job

Always provide specific evidence from the conversation to justify scores."""


@dataclass
class JTBDScore:
    """Scores for JTBD evaluation."""

    # Functional jobs
    diagnose: int  # How well did it assess GTM level?
    clarify: int   # How well did it explain gaps?
    produce: int   # How useful are the artifacts?
    prioritize: int  # How clear are next steps?

    # Emotional jobs
    confident: int  # Does user feel they have a strategy?
    validated: int  # Is the assessment credible?
    relieved: int   # Is complexity reduced?
    empowered: int  # Can they take action?

    # Quality metrics
    relevance: int      # How relevant to the specific company?
    specificity: int    # How specific vs generic?
    actionability: int  # How actionable are recommendations?

    reasoning: str  # Detailed reasoning

    @property
    def functional_avg(self) -> float:
        return (self.diagnose + self.clarify + self.produce + self.prioritize) / 4

    @property
    def emotional_avg(self) -> float:
        return (self.confident + self.validated + self.relieved + self.empowered) / 4

    @property
    def quality_avg(self) -> float:
        return (self.relevance + self.specificity + self.actionability) / 3

    @property
    def overall(self) -> float:
        return (self.functional_avg + self.emotional_avg + self.quality_avg) / 3


class LLMJudge:
    """LLM-as-Judge for semantic evaluation."""

    def __init__(self):
        self.client = Anthropic()

    def evaluate_conversation(
        self,
        company_url: str,
        company_name: str,
        conversation: list[dict],
        final_scorecard: str,
    ) -> JTBDScore:
        """Evaluate a GTM agent conversation against JTBD criteria."""

        # Format conversation for evaluation
        conv_text = "\n\n".join([
            f"**{msg['role'].upper()}**: {msg['content'][:1000]}"
            for msg in conversation
        ])

        prompt = f"""Evaluate this GTM Agent conversation against JTBD criteria.

## Company Being Evaluated
- URL: {company_url}
- Name: {company_name}

## JTBD Framework
{JTBD_CRITERIA}

## Conversation
{conv_text}

## Final Scorecard Output
{final_scorecard}

---

Evaluate each dimension (1-5 scale) with specific evidence:

1. FUNCTIONAL JOBS:
   - diagnose: How well did it assess their GTM level?
   - clarify: How well did it explain their gaps?
   - produce: How useful would the artifacts be?
   - prioritize: How clear are the next steps?

2. EMOTIONAL JOBS:
   - confident: Would they feel they have a real strategy?
   - validated: Is the assessment credible and trustworthy?
   - relieved: Does it reduce GTM complexity/overwhelm?
   - empowered: Can they take action immediately?

3. QUALITY METRICS:
   - relevance: How relevant to THIS specific company (not generic)?
   - specificity: How specific are recommendations (vs boilerplate)?
   - actionability: Can they execute on advice today?

Respond in this exact JSON format:
{{
    "diagnose": <1-5>,
    "clarify": <1-5>,
    "produce": <1-5>,
    "prioritize": <1-5>,
    "confident": <1-5>,
    "validated": <1-5>,
    "relieved": <1-5>,
    "empowered": <1-5>,
    "relevance": <1-5>,
    "specificity": <1-5>,
    "actionability": <1-5>,
    "reasoning": "<detailed reasoning with specific evidence>"
}}"""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=JUDGE_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse response
        content = response.content[0].text

        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            # Clean control characters from JSON
            json_str = json_match.group()
            json_str = re.sub(r'[\x00-\x1f\x7f-\x9f]', ' ', json_str)
            json_str = json_str.replace('\n', ' ').replace('\r', ' ')
            scores = json.loads(json_str)
            return JTBDScore(**scores)
        else:
            raise ValueError(f"Could not parse judge response: {content}")


class GTMAgentClient:
    """Client for interacting with GTM Agent via LangGraph API."""

    def __init__(self, base_url: str = "http://localhost:8123"):
        self.base_url = base_url
        self.thread_id = None
        self.conversation = []

    def create_thread(self) -> str:
        """Create a new conversation thread."""
        resp = requests.post(f"{self.base_url}/threads", json={})
        resp.raise_for_status()
        self.thread_id = resp.json()["thread_id"]
        self.conversation = []
        return self.thread_id

    def send_message(self, content: str, timeout: int = 90) -> str:
        """Send a message and wait for response."""
        if not self.thread_id:
            raise ValueError("No thread created")

        # Record user message
        self.conversation.append({"role": "user", "content": content})

        # Start run
        run_resp = requests.post(
            f"{self.base_url}/threads/{self.thread_id}/runs",
            json={
                "assistant_id": "gtm-agent",
                "input": {"messages": [{"role": "user", "content": content}]}
            }
        )
        run_resp.raise_for_status()
        run_id = run_resp.json()["run_id"]

        # Wait for completion
        for _ in range(timeout):
            status_resp = requests.get(
                f"{self.base_url}/threads/{self.thread_id}/runs/{run_id}"
            )
            status = status_resp.json().get("status")
            if status == "success":
                break
            elif status == "error":
                raise RuntimeError("Agent run failed")
            time.sleep(1)

        # Get response
        state_resp = requests.get(
            f"{self.base_url}/threads/{self.thread_id}/state"
        )
        messages = state_resp.json().get("values", {}).get("messages", [])

        # Find last AI message
        for msg in reversed(messages):
            if msg.get("type") == "ai":
                content = msg.get("content", "")
                if isinstance(content, str):
                    ai_response = content
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            ai_response = item.get("text", "")
                            break
                    else:
                        ai_response = str(content)
                else:
                    ai_response = str(content)

                self.conversation.append({"role": "assistant", "content": ai_response})
                return ai_response

        return ""

    def run_diagnostic_flow(
        self,
        company_url: str,
        q1_answer: str = "SMB Founders (1-50 employees)",
        q2_answer: str = "Pretty clear - we've validated it",
        q3_answer: str = "Pilots/design partners",
    ) -> str:
        """Run through complete diagnostic flow, return final scorecard."""

        # Start with URL
        self.send_message(f"Please analyze {company_url} and help me with GTM strategy")

        # Answer diagnostic questions
        self.send_message(q1_answer)
        self.send_message(q2_answer)
        final_response = self.send_message(q3_answer)

        return final_response


@pytest.fixture
def agent_client():
    """Create agent client."""
    return GTMAgentClient()


@pytest.fixture
def llm_judge():
    """Create LLM judge."""
    return LLMJudge()


# Test cases with real URLs
TEST_CASES = [
    {
        "url": "https://www.cashisclay.com",
        "name": "Cash is Clay",
        "description": "Personal finance / content creator",
    },
    {
        "url": "https://www.chaiwithjai.com",
        "name": "Chai with Jai",
        "description": "Tech content / developer education",
    },
    {
        "url": "https://www.princetonideaexchange.com",
        "name": "Princeton Idea Exchange",
        "description": "University innovation / entrepreneurship",
    },
    {
        "url": "https://www.langchain.com",
        "name": "LangChain",
        "description": "AI/ML developer tools",
    },
]


@pytest.mark.e2e
@pytest.mark.jtbd
@pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="Requires ANTHROPIC_API_KEY"
)
class TestJTBDEvaluation:
    """JTBD-based evaluation of GTM Agent workflows."""

    @pytest.mark.parametrize("test_case", TEST_CASES, ids=lambda x: x["name"])
    def test_url_workflow_jtbd(self, agent_client, llm_judge, test_case):
        """Test workflow against JTBD criteria for each URL."""

        # Run the workflow
        agent_client.create_thread()
        final_scorecard = agent_client.run_diagnostic_flow(test_case["url"])

        # Evaluate with LLM judge
        score = llm_judge.evaluate_conversation(
            company_url=test_case["url"],
            company_name=test_case["name"],
            conversation=agent_client.conversation,
            final_scorecard=final_scorecard,
        )

        # Print detailed results
        print(f"\n{'='*60}")
        print(f"JTBD EVALUATION: {test_case['name']}")
        print(f"URL: {test_case['url']}")
        print(f"{'='*60}")
        print(f"\nFUNCTIONAL JOBS (avg: {score.functional_avg:.1f}/5)")
        print(f"  Diagnose:   {score.diagnose}/5")
        print(f"  Clarify:    {score.clarify}/5")
        print(f"  Produce:    {score.produce}/5")
        print(f"  Prioritize: {score.prioritize}/5")
        print(f"\nEMOTIONAL JOBS (avg: {score.emotional_avg:.1f}/5)")
        print(f"  Confident:  {score.confident}/5")
        print(f"  Validated:  {score.validated}/5")
        print(f"  Relieved:   {score.relieved}/5")
        print(f"  Empowered:  {score.empowered}/5")
        print(f"\nQUALITY METRICS (avg: {score.quality_avg:.1f}/5)")
        print(f"  Relevance:     {score.relevance}/5")
        print(f"  Specificity:   {score.specificity}/5")
        print(f"  Actionability: {score.actionability}/5")
        print(f"\n{'='*60}")
        print(f"OVERALL SCORE: {score.overall:.1f}/5")
        print(f"{'='*60}")
        print(f"\nREASONING:\n{score.reasoning}")

        # Assertions - minimum acceptable scores
        assert score.functional_avg >= 3.0, f"Functional jobs score too low: {score.functional_avg}"
        assert score.emotional_avg >= 2.5, f"Emotional jobs score too low: {score.emotional_avg}"
        assert score.quality_avg >= 2.5, f"Quality metrics score too low: {score.quality_avg}"
        assert score.overall >= 3.0, f"Overall score too low: {score.overall}"

    def test_aggregate_jtbd_scores(self, agent_client, llm_judge):
        """Run all URLs and compute aggregate JTBD scores."""

        all_scores = []

        for test_case in TEST_CASES:
            try:
                agent_client.create_thread()
                final_scorecard = agent_client.run_diagnostic_flow(test_case["url"])

                score = llm_judge.evaluate_conversation(
                    company_url=test_case["url"],
                    company_name=test_case["name"],
                    conversation=agent_client.conversation,
                    final_scorecard=final_scorecard,
                )
                all_scores.append((test_case["name"], score))
            except Exception as e:
                print(f"Failed for {test_case['name']}: {e}")
                continue

        # Aggregate report
        print("\n" + "="*70)
        print("AGGREGATE JTBD EVALUATION REPORT")
        print("="*70)

        if not all_scores:
            pytest.skip("No successful evaluations")

        # Compute averages
        avg_functional = sum(s.functional_avg for _, s in all_scores) / len(all_scores)
        avg_emotional = sum(s.emotional_avg for _, s in all_scores) / len(all_scores)
        avg_quality = sum(s.quality_avg for _, s in all_scores) / len(all_scores)
        avg_overall = sum(s.overall for _, s in all_scores) / len(all_scores)

        print(f"\nSamples evaluated: {len(all_scores)}")
        print(f"\nAVERAGE SCORES:")
        print(f"  Functional Jobs: {avg_functional:.2f}/5")
        print(f"  Emotional Jobs:  {avg_emotional:.2f}/5")
        print(f"  Quality Metrics: {avg_quality:.2f}/5")
        print(f"  OVERALL:         {avg_overall:.2f}/5")

        print("\nPER-COMPANY BREAKDOWN:")
        for name, score in all_scores:
            print(f"  {name}: {score.overall:.1f}/5")

        # Find weakest dimensions
        all_dimensions = {}
        for _, score in all_scores:
            for dim in ['diagnose', 'clarify', 'produce', 'prioritize',
                       'confident', 'validated', 'relieved', 'empowered',
                       'relevance', 'specificity', 'actionability']:
                if dim not in all_dimensions:
                    all_dimensions[dim] = []
                all_dimensions[dim].append(getattr(score, dim))

        dim_avgs = {k: sum(v)/len(v) for k, v in all_dimensions.items()}
        sorted_dims = sorted(dim_avgs.items(), key=lambda x: x[1])

        print("\nWEAKEST DIMENSIONS (improvement opportunities):")
        for dim, avg in sorted_dims[:3]:
            print(f"  {dim}: {avg:.2f}/5")

        print("\nSTRONGEST DIMENSIONS:")
        for dim, avg in sorted_dims[-3:]:
            print(f"  {dim}: {avg:.2f}/5")

        assert avg_overall >= 3.0, f"Aggregate score too low: {avg_overall}"
