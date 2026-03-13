# Claw Agent — Developer Automation Agent

A local, modular automation agent that orchestrates workflows across Slack, GitHub, Jira, Confluence, Jenkins, and Gmail using LLM-powered reasoning via OpenClaw.

Compiles to a single Windows `.exe` via PyInstaller.

---

## Quick Start

### 1. Clone and install

```bash
cd developer-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in the credentials for the integrations you want to enable. At minimum, set:

| Variable | Purpose |
|----------|---------|
| `OPENCLAW_PROVIDER` | `openrouter`, `openai`, or `ollama` |
| `OPENCLAW_API_KEY` | API key for your chosen LLM provider |
| `OPENCLAW_MODEL` | Model identifier (e.g. `openai/gpt-4o`) |

Each integration (Slack, GitHub, Jira, etc.) is optional — the agent gracefully skips any integration whose credentials are not set.

### 3. Run the agent

**Interactive chat:**

```bash
python main.py chat
```

**Start the webhook server:**

```bash
python main.py webhook-server
```

**Start the agent daemon (same as webhook-server):**

```bash
python main.py run
```

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    CLI / Chat                         │
├──────────────────────────────────────────────────────┤
│                  Orchestrator                         │
│        (LLM Client  ·  Planner  ·  Memory)           │
├──────────────────────────────────────────────────────┤
│              Tool Registry                            │
├────────┬────────┬──────┬───────┬────────┬────────────┤
│ Slack  │ GitHub │ Jira │ Confl │Jenkins │   Gmail    │
├────────┴────────┴──────┴───────┴────────┴────────────┤
│         Event Bus  ←  Webhook Server                  │
├──────────────────────────────────────────────────────┤
│     Workflow Engine  (YAML-defined automations)       │
├──────────────────────────────────────────────────────┤
│   SQLite Database  ·  Secure Credential Store         │
└──────────────────────────────────────────────────────┘
```

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **Agent Core** | `agent/` | LLM client, orchestrator, planner, conversation memory |
| **Integrations** | `integrations/` | Slack, GitHub, Jira, Confluence, Jenkins, Gmail connectors |
| **Workflow Engine** | `workflows/` | Loads YAML workflows, executes action chains on events |
| **Event Bus** | `events/` | In-process pub/sub with topic-based routing |
| **Webhook Server** | `webhooks/` | FastAPI endpoints for GitHub, Jira, Jenkins, Slack |
| **CLI** | `cli/` | Rich-powered interactive chat interface |
| **Security** | `security/` | Secret loading, log redaction, webhook signature validation |
| **Database** | `database/` | SQLAlchemy models — events, workflow runs, summaries, tool outputs |

---

## Integrations

### Slack

| Tool | Description |
|------|-------------|
| `slack.send_message` | Post a message to a channel |
| `slack.read_channel_history` | Read recent channel messages |

**Required env vars:** `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`

### GitHub

| Tool | Description |
|------|-------------|
| `github.create_issue` | Create an issue |
| `github.summarize_pull_request` | Get PR details |
| `github.comment_on_pr` | Comment on a PR |
| `github.create_branch` | Create a branch |
| `github.get_repo_activity` | Recent commits, PRs, issues |

**Required env vars:** `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`

### Jira

| Tool | Description |
|------|-------------|
| `jira.create_ticket` | Create a ticket |
| `jira.update_ticket` | Update ticket fields |
| `jira.link_github_issue` | Add GitHub remote link |
| `jira.get_ticket_details` | Get ticket details |

**Required env vars:** `JIRA_URL`, `JIRA_USER`, `JIRA_API_TOKEN`

### Confluence

| Tool | Description |
|------|-------------|
| `confluence.search_docs` | CQL search |
| `confluence.summarize_page` | Get page content |
| `confluence.create_page` | Create a page |

**Required env vars:** `CONFLUENCE_URL`, `CONFLUENCE_USER`, `CONFLUENCE_API_TOKEN`

### Jenkins

| Tool | Description |
|------|-------------|
| `jenkins.trigger_build` | Trigger a build |
| `jenkins.get_build_status` | Get build status |
| `jenkins.fetch_build_logs` | Get console output |

**Required env vars:** `JENKINS_URL`, `JENKINS_USER`, `JENKINS_API_TOKEN`

### Gmail

| Tool | Description |
|------|-------------|
| `gmail.read_emails` | Search and read emails |
| `gmail.summarize_thread` | Get thread messages |
| `gmail.send_email` | Send an email |
| `gmail.extract_action_items` | Extract text for LLM processing |

**Required:** `credentials.json` (OAuth client) and completing the OAuth flow to generate `token.json`.

---

## Workflows

Workflows are YAML files in the `workflows/` directory. They fire automatically when a matching event arrives via webhook.

### Example: PR Opened

```yaml
name: pr_opened_workflow
trigger: github.pull_request.opened
actions:
  - tool: github.summarize_pull_request
    description: Summarize the pull request
  - tool: slack.send_message
    description: Post PR summary to Slack
    args:
      channel: "#dev-notifications"
  - tool: jira.link_github_issue
    description: Link the PR to the related Jira ticket
```

### Example: Build Failed

```yaml
name: build_failed_workflow
trigger: jenkins.build.failed
actions:
  - tool: jenkins.fetch_build_logs
    description: Fetch the failed build logs
  - tool: agent.summarize
    description: Summarize the failure using LLM
  - tool: slack.send_message
    description: Post failure summary to Slack
    args:
      channel: "#build-alerts"
```

### Adding a new workflow

1. Create a `.yaml` file in `workflows/`
2. Set `trigger` to the event type you want to match
3. List the `actions` (tools) to execute in order
4. Restart the agent

---

## Webhook Server

The webhook server runs on `http://localhost:8080` by default.

| Endpoint | Source |
|----------|--------|
| `POST /webhooks/github` | GitHub push/PR/issue events |
| `POST /webhooks/jira` | Jira issue events |
| `POST /webhooks/jenkins` | Jenkins build notifications |
| `POST /webhooks/slack` | Slack event subscriptions |
| `GET /health` | Health check |
| `GET /docs` | OpenAPI / Swagger UI |

All endpoints validate webhook signatures when the corresponding secret is configured.

---

## LLM Configuration

The agent supports three LLM providers via the OpenClaw abstraction:

| Provider | `OPENCLAW_PROVIDER` | Notes |
|----------|---------------------|-------|
| OpenRouter | `openrouter` | Default. Supports many models. |
| OpenAI | `openai` | Direct OpenAI API. |
| Ollama | `ollama` | Local models. Set `OPENCLAW_BASE_URL` if non-default. |

---

## Security

- All secrets loaded from environment variables / `.env` — never hardcoded.
- Webhook endpoints validate HMAC signatures.
- Logs are filtered to redact tokens and API keys.
- `.env` and credential files are `.gitignore`d.
- Each integration uses the minimum required scopes.

---

## Database

SQLite stores all operational data locally:

| Table | Contents |
|-------|----------|
| `events` | All incoming events with type, source, payload |
| `workflow_runs` | Workflow execution records with status and results |
| `cached_summaries` | LLM-generated summaries keyed for reuse |
| `tool_outputs` | Inputs and outputs of every tool call |

Default location: `data/agent.db`

---

## Building the Windows Executable

```bash
pip install pyinstaller
pyinstaller --onefile main.py --name claw-agent
```

The output binary will be in `dist/claw-agent.exe`.

### Usage after build

```bash
claw-agent.exe chat
claw-agent.exe run
claw-agent.exe webhook-server
```

---

## Project Structure

```
developer-agent/
├── agent/
│   ├── orchestrator.py      # LLM client, tool registry, main orchestrator
│   ├── planner.py           # Action plan decomposition
│   └── memory.py            # Conversation history
├── integrations/
│   ├── slack.py
│   ├── github_integration.py
│   ├── jira_integration.py
│   ├── confluence.py
│   ├── jenkins.py
│   └── gmail.py
├── workflows/
│   ├── engine.py            # Workflow execution engine
│   ├── loader.py            # YAML workflow parser
│   ├── pr_opened.yaml
│   ├── build_failed.yaml
│   └── jira_created.yaml
├── events/
│   ├── bus.py               # Async event bus
│   └── types.py             # Event models
├── webhooks/
│   └── server.py            # FastAPI webhook endpoints
├── security/
│   └── secrets.py           # Credential loading, redaction, signature validation
├── database/
│   └── models.py            # SQLAlchemy models and session management
├── cli/
│   └── chat.py              # Interactive chat interface
├── config/
│   └── config.yaml
├── logs/
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py                  # Entry point and CLI commands
└── README.md
```
