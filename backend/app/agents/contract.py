"""Step 1 agents: the two analysts who lay out the facts before the debate."""
from pydantic import BaseModel, Field

from app.agents.gemini import ask


class AgentOutput(BaseModel):
    text: str = Field(description="2 to 4 punchy sentences.")
    sources: list[str] = Field(description="1 to 3 labels copied from the allowed source labels.")


FINANCIAL_ANALYST = """You are the Financial Analyst. Summarize the company's numbers in this scenario:
EBITDA, free cash flow, debt against cash, leverage and interest coverage. If the scenario differs from
the reported numbers, say what changed. State facts only. Do not give an opinion on whether to lend."""

# Rules come from the company config for now. When we fetch real credit agreements, this agent
# will read the contract HTML and extract the rules itself (and that result gets cached per company).
CONTRACT_ANALYST = """You are the Contract Analyst. State each loan rule from the credit agreement with
its threshold, then say whether the company passes or fails it in this scenario, using the value given.
State facts only. Do not give an opinion on whether to lend. Cite the credit agreement sections."""


async def run_financial_analyst(briefing: str) -> AgentOutput:
    return await ask(FINANCIAL_ANALYST, briefing, AgentOutput)


async def run_contract_analyst(briefing: str) -> AgentOutput:
    return await ask(CONTRACT_ANALYST, briefing, AgentOutput)
