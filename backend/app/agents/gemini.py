"""One place that talks to Gemini. Every agent goes through ask()."""
import os
from typing import TypeVar

from google import genai
from google.genai import types
from pydantic import BaseModel

Schema = TypeVar("Schema", bound=BaseModel)

SHARED_RULES = """You sit on a credit fund's committee deciding whether to lend to a company.
Use ONLY the numbers in the briefing. Never invent, estimate or recompute a figure.
Quote dollar amounts and ratios exactly as the briefing shows them (for example $350M, $4.36B, 5.71x).
Write 2 to 4 short, punchy sentences in plain English, the way a sharp analyst talks in a meeting.
No bullet points, no hedging, no preamble, no legalese. Say "the 5.00x cap", not "the maximum leverage ratio threshold".
Do not write section numbers in the text; put them in `sources` instead.
For `sources`, pick 1 to 3 labels from the "Allowed source labels" list in the briefing, copied exactly."""


async def ask(role: str, briefing: str, schema: type[Schema]) -> Schema:
    """Send one agent's instructions plus the shared briefing; get back validated JSON."""
    client = genai.Client(
        api_key=os.environ["GEMINI_API_KEY"],
        # Gemini often answers 503 "high demand" for a moment, so retry before giving up.
        http_options=types.HttpOptions(
            timeout=30_000,  # milliseconds, per attempt
            retry_options=types.HttpRetryOptions(attempts=4, initial_delay=1.0, max_delay=4.0),
        ),
    )
    response = await client.aio.models.generate_content(
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite"),
        contents=briefing,
        config=types.GenerateContentConfig(
            system_instruction=f"{SHARED_RULES}\n\n{role}",
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.3,
        ),
    )
    return schema.model_validate_json(response.text)
