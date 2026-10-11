"""The committee as a LangGraph pipeline.

Step 1: financial_analyst + contract_analyst (parallel)
Step 2: bull + bear (parallel)
Step 3: chair
Each agent announces when it starts and finishes; those announcements become the SSE events.
"""
from collections.abc import AsyncIterator
from typing import TypedDict

from langgraph.config import get_stream_writer
from langgraph.graph import END, START, StateGraph

from app.agents import contract, debate
from app.agents.briefing import build_briefing
from app.numbers.calculator import calculate
from app.numbers.routes import load_company


class CommitteeState(TypedDict, total=False):
    ticker: str
    earnings_drop_pct: float
    refi_rate_pct: float
    briefing: str
    financial_analyst: str
    contract_analyst: str
    bull: str
    bear: str


def started(agent: str) -> None:
    get_stream_writer()({"type": "agent_started", "data": {"agent": agent}})


def done(agent: str, output: contract.AgentOutput) -> None:
    get_stream_writer()({"type": "agent_done", "data": {"agent": agent, "text": output.text, "sources": output.sources}})


async def financial_analyst(state: CommitteeState) -> CommitteeState:
    started("financial_analyst")
    output = await contract.run_financial_analyst(state["briefing"])
    done("financial_analyst", output)
    return {"financial_analyst": output.text}


def briefing_for(state: CommitteeState) -> str:
    company = load_company(state["ticker"])
    calc = calculate(company, state["earnings_drop_pct"], state["refi_rate_pct"])
    return build_briefing(company, calc, state["earnings_drop_pct"], state["refi_rate_pct"])


async def contract_analyst(state: CommitteeState) -> CommitteeState:
    started("contract_analyst")
    # First run for a company: read the real contract (cached after that), then rebuild the
    # briefing so everyone downstream sees the full quotes and the threshold schedule.
    await contract.ensure_contract_is_read(load_company(state["ticker"]))
    briefing = briefing_for(state)
    output = await contract.run_contract_analyst(briefing)
    done("contract_analyst", output)
    return {"contract_analyst": output.text, "briefing": briefing}


def analyst_notes(state: CommitteeState) -> dict[str, str]:
    return {"Financial Analyst": state["financial_analyst"], "Contract Analyst": state["contract_analyst"]}


async def bull(state: CommitteeState) -> CommitteeState:
    started("bull")
    output = await debate.run_bull(state["briefing"], analyst_notes(state))
    done("bull", output)
    return {"bull": output.text}


async def bear(state: CommitteeState) -> CommitteeState:
    started("bear")
    output = await debate.run_bear(state["briefing"], analyst_notes(state))
    done("bear", output)
    return {"bear": output.text}


async def chair(state: CommitteeState) -> CommitteeState:
    started("chair")
    notes = analyst_notes(state) | {"Bull": state["bull"], "Bear": state["bear"]}
    output = await debate.run_chair(state["briefing"], notes)
    done("chair", output)
    get_stream_writer()({"type": "verdict", "data": {"decision": output.decision, "text": output.text}})
    return {}


def build_graph():
    graph = StateGraph(CommitteeState)
    for node in (financial_analyst, contract_analyst, bull, bear, chair):
        graph.add_node(node.__name__, node)
    graph.add_edge(START, "financial_analyst")
    graph.add_edge(START, "contract_analyst")
    # A list of sources means "wait for all of them", which is what makes the steps.
    graph.add_edge(["financial_analyst", "contract_analyst"], "bull")
    graph.add_edge(["financial_analyst", "contract_analyst"], "bear")
    graph.add_edge(["bull", "bear"], "chair")
    graph.add_edge("chair", END)
    return graph.compile()


COMMITTEE = build_graph()


async def run_committee(ticker: str, earnings_drop_pct: float, refi_rate_pct: float) -> AsyncIterator[dict]:
    """Yields {"type": ..., "data": ...} events in the SSE format from CLAUDE.md."""
    state: CommitteeState = {"ticker": ticker, "earnings_drop_pct": earnings_drop_pct, "refi_rate_pct": refi_rate_pct}
    state["briefing"] = briefing_for(state)
    async for event in COMMITTEE.astream(state, stream_mode="custom"):
        yield event
