"""Step 1 agents: the two analysts who lay out the facts before the debate.

The Contract Analyst also reads the real credit agreement: read_contract() downloads it from
SEC EDGAR, finds the covenant sections, and has Gemini pull out the exact sentences. The result
is cached in data/cache/, so this happens once per company.
"""
import asyncio
import json
import logging
import os
import re

import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel, Field

from app.agents.gemini import ask
from app.models import Company
from app.numbers.routes import CACHE, contract_cache_path

logger = logging.getLogger("uvicorn.error")


class AgentOutput(BaseModel):
    text: str = Field(description="2 to 4 punchy sentences.")
    sources: list[str] = Field(description="1 to 3 labels copied from the allowed source labels.")


FINANCIAL_ANALYST = """You are the Financial Analyst. Summarize the company's numbers in this scenario:
EBITDA, free cash flow, debt against cash, leverage and interest coverage. If the scenario differs from
the reported numbers, say what changed. State facts only. Do not give an opinion on whether to lend."""

CONTRACT_ANALYST = """You are the Contract Analyst. State each loan rule from the credit agreement with
its threshold, then say whether the company passes or fails it in this scenario, using the value given.
State facts only. Do not give an opinion on whether to lend. Cite the credit agreement sections."""


async def run_financial_analyst(briefing: str) -> AgentOutput:
    return await ask(FINANCIAL_ANALYST, briefing, AgentOutput)


async def run_contract_analyst(briefing: str) -> AgentOutput:
    return await ask(CONTRACT_ANALYST, briefing, AgentOutput)


# ---- Reading the real contract -------------------------------------------------------------

class ThresholdRow(BaseModel):
    year: int | None = Field(description="Calendar year the period ends in; for an 'and thereafter' row, the year it starts. Null if the rule has one fixed ratio.")
    threshold: float = Field(description="The ratio as a number, e.g. 4.75 for 4.75:1.00.")


class ExtractedRule(BaseModel):
    section: str = Field(description="Section number, e.g. 9.08")
    quote: str = Field(description="The full covenant sentence, copied character for character.")
    thresholds: list[ThresholdRow]


class ContractExtraction(BaseModel):
    rules: list[ExtractedRule]


EXTRACTOR = """You are a paralegal copying covenants out of a credit agreement. For each section in the
excerpt, return the FULL covenant sentence: start at the first word after the section heading and stop
at the end of that sentence (a period, or a colon if the sentence introduces a table). Copy it character
for character. Do not fix typos, do not paraphrase, do not add or drop a word, do not include the heading.
Then list the ratio thresholds: one row per period if there is a table of periods, otherwise a single row
with year null."""


def normalize(text: str) -> str:
    """Collapse whitespace so a quote can be compared with the document."""
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # SEC amendments are often blacklines: struck-through text is deleted wording, so drop it.
    for deleted in soup.find_all(["strike", "s", "del"]):
        deleted.decompose()
    return normalize(soup.get_text(" "))


async def fetch_contract_text(company: Company) -> str:
    """Download the covenant document once; keep the plain text in data/cache/."""
    text_path = CACHE / f"{company.ticker}_contract.txt"
    if text_path.exists():
        return text_path.read_text()
    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        response = await client.get(company.covenant_url, headers={"User-Agent": os.environ["SEC_USER_AGENT"]})
        response.raise_for_status()
    text = await asyncio.to_thread(html_to_text, response.text)  # parsing 2MB of HTML takes a few seconds
    CACHE.mkdir(parents=True, exist_ok=True)
    text_path.write_text(text)
    return text


def find_section(text: str, section: str) -> str:
    """The body of e.g. Section 9.08: from its heading to the next section heading."""
    # The last match skips the table of contents; a capital letter after the number means a heading.
    headings = list(re.finditer(rf"Section {re.escape(section)}\s+[A-Z]", text))
    if not headings:
        raise ValueError(f"Section {section} not found in the contract")
    start = headings[-1].start()
    following = re.search(r"Section \d+\.\d+\s+[A-Z]", text[start + 20:])
    end = start + 20 + following.start() if following else start + 6000
    return text[start:min(end, start + 6000)]


async def read_contract(company: Company) -> None:
    """Extract the loan rules from the contract, check them, and write the cache file."""
    text = await fetch_contract_text(company)
    excerpts = "\n\n".join(find_section(text, rule.section) for rule in company.rules)
    extraction = await ask(EXTRACTOR, f"EXCERPT FROM THE CREDIT AGREEMENT:\n\n{excerpts}", ContractExtraction)

    test_year = company.fiscal_year + 1  # the next covenant tests happen in the year after the 10-K
    cached_rules = []
    for rule in company.rules:
        found = next((item for item in extraction.rules if item.section.strip() == rule.section), None)
        if found is None or not found.thresholds:
            raise ValueError(f"Gemini returned nothing for Section {rule.section}")
        quote = normalize(found.quote)
        if quote not in text:
            raise ValueError(f"Quote for Section {rule.section} is not in the document: {quote[:80]!r}")
        schedule = sorted((row for row in found.thresholds if row.year is not None), key=lambda row: row.year)
        in_force = [row for row in schedule if row.year <= test_year] or schedule or found.thresholds
        threshold = in_force[0].threshold if len(schedule) < 2 else in_force[-1].threshold
        # The hand-checked config is the referee: if Gemini reads a different limit, don't trust the read.
        if abs(threshold - rule.threshold) > 0.001:
            raise ValueError(f"Section {rule.section}: contract read says {threshold}, config says {rule.threshold}")
        cached_rules.append({
            "type": rule.type, "section": rule.section, "quote": quote, "threshold": threshold,
            "schedule": [{"year": row.year, "threshold": row.threshold} for row in schedule] if len(schedule) > 1 else [],
        })
    contract_cache_path(company.ticker).write_text(json.dumps(
        {"source_url": company.covenant_url, "quotes_verified_in_document": True, "rules": cached_rules}, indent=2) + "\n")


async def ensure_contract_is_read(company: Company) -> None:
    """Read the contract if we haven't yet. On any failure, log it and keep the config rules."""
    if not company.covenant_url or contract_cache_path(company.ticker).exists():
        return
    try:
        await read_contract(company)
        logger.info("Read the credit agreement for %s", company.ticker)
    except Exception:
        logger.exception("Could not read the credit agreement for %s; using the rules in its config", company.ticker)
