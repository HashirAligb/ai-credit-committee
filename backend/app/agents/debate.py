"""Step 2 and 3 agents: Bull and Bear argue, then the Chair decides."""
from typing import Literal

from pydantic import Field

from app.agents.contract import AgentOutput
from app.agents.gemini import ask


class ChairOutput(AgentOutput):
    decision: Literal["lend", "dont_lend", "lend_with_conditions"]


BULL = """You are the Bull. Argue TO LEND, always, whatever the numbers. Open with "Lend." when the loan
rules pass. When rules fail, make the strongest honest case anyway (cash flow that remains, a temporary
dip, a waiver with tighter terms) without denying the breach."""

BEAR = """You are the Bear. Argue AGAINST lending, always, whatever the numbers. Open with "Don't lend."
When rules fail, lead with the breaches. When rules pass, attack the maturity wall: the debt coming due
versus the cash available that year, and the dependence on refinancing. If the briefing says a limit
tightens over time, use it: say what it tightens to, when, and what debt comes due that same year."""

CHAIR = """You are the Committee Chair. Weigh the Bull and the Bear and decide. Decide like this:
- If ANY loan rule FAILS in this scenario: decision is "dont_lend". A fund does not lend into a covenant breach.
- If every rule passes with comfortable headroom (more than 10% away from its threshold): decision is "lend".
  A maturity that needs refinancing is normal for a borrower in good standing and is not, alone, a reason for conditions.
- If every rule passes but one is within 10% of its threshold: decision is "lend_with_conditions", and name the condition.
Open `text` with "Lend.", "Don't lend." or "Lend with conditions." Then give the numbers that drove it and
one line on the losing side's best point. Never say "pass" to mean decline; it reads like a rule passing."""


def with_notes(briefing: str, notes: dict[str, str]) -> str:
    """Append what earlier agents said so later agents can respond to it."""
    lines = "\n".join(f"- {name}: {text}" for name, text in notes.items())
    return f"{briefing}\n\nWhat the committee has said so far:\n{lines}"


async def run_bull(briefing: str, notes: dict[str, str]) -> AgentOutput:
    return await ask(BULL, with_notes(briefing, notes), AgentOutput)


async def run_bear(briefing: str, notes: dict[str, str]) -> AgentOutput:
    return await ask(BEAR, with_notes(briefing, notes), AgentOutput)


async def run_chair(briefing: str, notes: dict[str, str]) -> ChairOutput:
    return await ask(CHAIR, with_notes(briefing, notes), ChairOutput)
