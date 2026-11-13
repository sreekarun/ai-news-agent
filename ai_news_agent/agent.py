"""AI News Agent: source-cited briefings on AI industry news.

Layout:
  root_agent, named ai_news_agent (briefing editor)
    ├─ get_current_date      function tool, so "today" / "this week" are concrete
    └─ news_researcher       AgentTool wrapping Gemini's built-in google_search and
                             url_context. Built-in tools can't share an agent with
                             function tools, so research lives in its own agent.
"""

import datetime
import os
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import AgentTool, google_search, url_context
from google.genai import types

MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.8-flash")
# gemini-3.8-flash is only served from `global`, while Agent Runtime sets
# GOOGLE_CLOUD_LOCATION to its region, so model calls get their own location.
MODEL_LOCATION = os.getenv("MODEL_LOCATION", "global")
NEWS_TIMEZONE = os.getenv("NEWS_TIMEZONE", "America/Los_Angeles")


def _model() -> Gemini:
    return Gemini(
        model=MODEL_NAME,
        client_kwargs={"location": MODEL_LOCATION},
        retry_options=types.HttpRetryOptions(attempts=3),
    )


def get_current_date() -> dict:
    """Get today's date and time, so relative ranges like "today" or "this week" can be resolved.

    Returns:
        A dict with status, the ISO date, weekday, and timezone.
    """
    now = datetime.datetime.now(ZoneInfo(NEWS_TIMEZONE))
    return {
        "status": "success",
        "date": now.date().isoformat(),
        "weekday": now.strftime("%A"),
        "time": now.strftime("%H:%M"),
        "timezone": NEWS_TIMEZONE,
    }


news_researcher = Agent(
    name="news_researcher",
    model=_model(),
    description=(
        "Searches the web for recent AI news and reads specific article URLs. "
        "Give it a focused query including a date range."
    ),
    instruction="""You research AI industry news.

- Use google_search to find recent coverage. Use url_context to read a specific URL.
- Return a list of findings. For each: headline, publisher, publication date,
  URL, and 2-4 factual sentences of what happened.
- Prefer primary sources (company blogs, research papers, regulators, filings)
  and established outlets. Note when a claim appears in only one source.
- Only report what the sources say. Never invent dates, numbers, quotes or URLs.
  If nothing relevant is found, say so.""",
    tools=[google_search, url_context],
)


root_agent = Agent(
    # Keep in sync with create_params.root_agent_name in agents-cli-manifest.yaml.
    # It's also the A2A agent card's name, which is how Agent Registry lists
    # this agent (the scaffold default "root_agent" showed up there as-is).
    name="ai_news_agent",
    model=_model(),
    description="Briefs users on the most important recent AI news, with sources.",
    instruction="""You are an AI news editor. You help people keep up with the AI industry:
models and products, research, funding and deals, policy and regulation, chips
and infrastructure.

How to work:
1. Call get_current_date first whenever the request involves time ("today",
   "this week", "latest"). Default window: the last 48 hours.
2. Call news_researcher with focused queries that include the date range. Run
   several queries for a broad briefing (e.g. models, research, funding, policy).
3. Rank stories by impact on the AI field, merge duplicates, and drop anything
   outside the window.

What you can do:
- Daily briefing: the top 5-7 stories, most important first.
- Topic tracking: the same, filtered to a theme or company.
- Explainer: background and why it matters, for one story or concept.
- Fact-check: compare sources; label claims as confirmed, disputed or unconfirmed.

Format each story as:
**Headline**: 2-3 sentence summary.
*Why it matters:* one sentence.
Source: [Publisher](URL), date

Rules:
- Every story needs a source link and a date that came from news_researcher.
  Never invent stories, links, dates or numbers. On a slow news day, return
  fewer stories rather than padding.
- Summarize in your own words; don't reproduce article text.
- If a request isn't about AI news, say briefly what you cover and offer a
  related AI-news angle.""",
    tools=[
        get_current_date,
        # Don't set propagate_grounding_metadata=True: on Agent Runtime the
        # propagated metadata reaches VertexAiSessionService.append_event as a
        # dict and the run crashes ('dict' object has no attribute 'model_dump').
        # Sources are already in the researcher's text.
        AgentTool(agent=news_researcher),
    ],
)

app = App(
    root_agent=root_agent,
    name="ai_news_agent",
)
