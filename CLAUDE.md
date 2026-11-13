# Coding Agent Guide

## Prerequisites

Install the CLI (one-time):
```bash
uv tool install google-agents-cli
```

---

## Development Phases

### Phase 1: Understand Requirements
Before writing any code, understand the project's requirements, constraints, and success criteria.

### Phase 2: Build and Implement
Implement agent logic in `ai_news_agent/`. Use `agents-cli playground` for interactive testing. Iterate based on user feedback.

### Phase 3: The Evaluation Loop (Main Iteration Phase)
Start with 1-2 eval cases, run `agents-cli eval run`, iterate by making changes and rerunning it until satisfied. Expect 5-10+ iterations. Once you have a baseline, reach for `agents-cli eval compare` (regression diffs), `agents-cli eval analyze` (cluster failure modes), and `agents-cli eval optimize` (auto-tune prompts). See the **Evaluation Guide** for metrics, dataset schema, LLM-as-judge config, and common gotchas.

### Phase 4: Pre-Deployment Tests
Run `uv run pytest tests/unit tests/integration`. Fix issues until all tests pass.

### Phase 5: Deploy to Dev
**Requires explicit human approval.** Run `agents-cli deploy` only after user confirms. See the **Deployment Guide** for details.

### Phase 6: Production Deployment
Ask the user: Option A (simple single-project) or Option B (full CI/CD pipeline with `agents-cli infra cicd`).

## Development Commands

| Command | Purpose |
|---------|---------|
| `agents-cli playground` | Interactive local testing |
| `uv run pytest tests/unit tests/integration` | Run unit and integration tests |
| `agents-cli eval dataset synthesize` | Synthesize multi-turn eval scenarios for your agent |
| `agents-cli eval run` | Run the agent over the eval dataset and grade the traces |
| `agents-cli eval generate` / `agents-cli eval grade` | Decoupled form: produce traces, then grade them |
| `agents-cli eval compare` | Compare two grade-results files (regression check) |
| `agents-cli eval analyze` | Cluster failure modes from grade results |
| `agents-cli eval metric list` | List built-in metrics available in the SDK |
| `agents-cli eval optimize` | Auto-tune agent prompts using eval data |
| `agents-cli lint` | Check code quality |
| `agents-cli infra single-project` | Set up project infrastructure (Terraform) |
| `agents-cli deploy` | Deploy to dev |
| `agents-cli scaffold enhance` | Add deployment target or CI/CD to project |
| `agents-cli scaffold upgrade` | Upgrade project to latest version |

---

## Operational Guidelines for Coding Agents

- **Code preservation**: Only modify code directly targeted by the user's request. Preserve all surrounding code, config values (e.g., `model`), comments, and formatting.
- **NEVER change the model** unless explicitly asked.
- **Model 404 errors**: the model is only served from `global`. Check `MODEL_LOCATION`, not the model name. On Agent Runtime, `GOOGLE_CLOUD_LOCATION` is the region, which is why `MODEL_LOCATION` exists.
- **ADK tool imports**: Import the tool instance, not the module: `from google.adk.tools.load_web_page import load_web_page`
- **Run Python with `uv`**: `uv run python script.py`. Run `agents-cli install` first.
- **Stop on repeated errors**: If the same error appears 3+ times, fix the root cause instead of retrying.
- **Terraform conflicts** (Error 409): Use `terraform import` instead of retrying creation.

---

## This project

AI news agent: source-cited briefings on AI industry news (daily briefing, topic
tracking, explainers, fact-checks). Sibling of `sreekarun/adk-chatbot`, deployed
to the same staging/prod projects as a separate Agent Runtime (display name
`ai-news-agent`).

- `ai_news_agent/agent.py`: `root_agent` (editor) with `get_current_date` and
  `AgentTool(news_researcher)`. `news_researcher` holds the built-in
  `google_search` + `url_context`. Built-in tools can't share an agent with
  function tools, so keep that split.
- Config: `MODEL_NAME` (default `gemini-3.8-flash`), `MODEL_LOCATION` (default
  `global`), `NEWS_TIMEZONE` (default `America/Los_Angeles`). Add new vars to
  `.env.example`.
- Search grounding is billed per grounded request, on top of model tokens.

## Deployment: GitHub Actions + Terraform only

- **Never run `agents-cli deploy` against staging or prod by hand.** PR → merge to
  `main` → *Deploy to Staging* → approval → *Deploy to Production*.
- Region `us-east4`. `sreeai-noorg` is the local dev project only.
- Infra: `deployment/terraform/cicd/`, applied with `agents-cli infra cicd`
  (plan first; `--apply` only with the user's go-ahead). It shares the staging and
  prod projects with `adk-chatbot`, so check every plan for changes to resources
  that project owns.
- Runtimes use Agent Identity: don't pass `--service-account` in the workflows.
  Any Terraform change to the runtime resource resets its code to the placeholder;
  follow it with a pipeline deploy.
- Runtime size comes from the workflow deploy flags: Agent Runtime minimums for
  the PoC (`--min-instances 0 --max-instances 1 --concurrency 3 --cpu 1
  --memory 1Gi`). `service.tf` matches, but Terraform only uses it at creation.
- Workflows set `GOOGLE_GENAI_USE_ENTERPRISE=true` and remove
  `GOOGLE_GENAI_USE_VERTEXAI` (both set raises an error), and set
  `GCSFS_EXPERIMENTAL_ZB_HNS_SUPPORT=false` (the bucket-type lookup 401s under
  Agent Identity).
- Keep the committed `deployment_metadata.json` at `null` values.
- Don't apply `deployment/terraform/single-project/`.
