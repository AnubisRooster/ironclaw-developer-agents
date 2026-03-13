# Claw Agent — Developer Automation Agent

A local developer automation agent that synchronizes workflows between Slack, GitHub, Jira, Confluence, Jenkins, and Gmail. Powered by **IronClaw**, the Rust-based OpenClaw runtime, as the AI reasoning engine.

Uses **PostgreSQL** as the primary database. Compiles to a single Windows `.exe` via PyInstaller.

---

## Architecture

```
Python Orchestrator
     │
     │  HTTP / JSON
     ▼
IronClaw Runtime (Rust)      ← AI reasoning engine
     │
     ▼
LLM Provider
```

All reasoning — prompt interpretation, planning, tool selection, and summarization — is delegated to the IronClaw runtime. The Python platform handles integrations, workflows, event processing, webhook handling, and tool execution.

```
┌──────────────────────────────────────────────────────┐
│                    CLI / Chat                         │
├──────────────────────────────────────────────────────┤
│                  Orchestrator                         │
│     (IronClaw Client  ·  Planner  ·  Memory)         │
├──────────────────────────────────────────────────────┤
│            Tool Schema Registry                       │
├────────┬────────┬──────┬───────┬────────┬────────────┤
│ Slack  │ GitHub │ Jira │ Confl │Jenkins │   Gmail    │
├────────┴────────┴──────┴───────┴────────┴────────────┤
│         Event Bus  ←  Webhook Server                  │
├──────────────────────────────────────────────────────┤
│     Workflow Engine  (YAML-defined automations)       │
├──────────────────────────────────────────────────────┤
│  PostgreSQL Database  ·  Secure Credential Store      │
└──────────────────────────────────────────────────────┘
```

### Components

| Component | Location | Purpose |
|-----------|----------|---------|
| **IronClaw Client** | `agent/ironclaw_client.py` | HTTP client for the IronClaw Rust runtime |
| **Orchestrator** | `agent/orchestrator.py` | Coordinates IronClaw, tool execution, and memory |
| **Tool Schema Registry** | `tools/registry.py` | Dynamic tool registration with JSON schemas |
| **Integrations** | `integrations/` | Slack, GitHub, Jira, Confluence, Jenkins, Gmail connectors |
| **Workflow Engine** | `workflows/` | Loads YAML workflows, executes action chains on events |
| **Event Bus** | `events/` | In-process async pub/sub with topic-based routing |
| **Webhook Server** | `webhooks/` | FastAPI endpoints for GitHub, Jira, Jenkins, Slack |
| **CLI** | `cli/` | Rich-powered interactive chat interface |
| **Security** | `security/` | Secret loading, log redaction, webhook signature validation |
| **Database** | `database/` | PostgreSQL via SQLAlchemy — events, workflows, tool results, memory |

---

## Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL running locally
- IronClaw runtime running on `http://localhost:9090`

### 2. Clone and install

```bash
cd ironclaw-developer-agent
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set up PostgreSQL

```bash
createdb clawagent
```

Or use Docker:

```bash
docker run -d --name claw-postgres \
  -e POSTGRES_USER=claw \
  -e POSTGRES_PASSWORD=claw \
  -e POSTGRES_DB=clawagent \
  -p 5432:5432 \
  postgres:16
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and set at minimum:

| Variable | Purpose |
|----------|---------|
| `IRONCLAW_URL` | URL of IronClaw runtime (default: `http://localhost:9090`) |
| `DATABASE_URL` | PostgreSQL connection string |

Each integration (Slack, GitHub, Jira, etc.) is optional — the agent gracefully skips any integration whose credentials are not set.

### 5. Run the agent

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

## IronClaw Runtime

IronClaw is the Rust variant of OpenClaw and serves as the AI reasoning engine. The Python application communicates with it via HTTP API calls.

**IronClaw is responsible for:**
- Prompt interpretation
- Planning actions
- Selecting tools
- Summarization

**The Python platform is responsible for:**
- Integration connectors
- Workflow execution
- Event processing
- Webhook handling
- Tool execution

The orchestrator sends conversation messages and available tool schemas to IronClaw. IronClaw returns either a text response or an `actions` list of tool calls to execute.

---

## Tool Schema Registry

Every integration registers its tools with JSON Schema definitions. IronClaw queries this registry to understand available capabilities.

Example tool schema:

```json
{
  "name": "github.summarize_pr",
  "description": "Summarize a GitHub pull request",
  "parameters": {
    "type": "object",
    "properties": {
      "repo": {"type": "string"},
      "pr_number": {"type": "integer"}
    },
    "required": ["repo", "pr_number"]
  }
}
```

The registry supports: `register_tool()`, `get_all_tools()`, `execute_tool()`.

---

## Integrations

### Slack

| Tool | Description |
|------|-------------|
| `slack.send_message` | Post a message to a channel |
| `slack.read_channel` | Read recent channel messages |

**Required env vars:** `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`

### GitHub

| Tool | Description |
|------|-------------|
| `github.create_issue` | Create an issue |
| `github.summarize_pr` | Summarize a pull request |
| `github.comment_pr` | Comment on a PR |
| `github.create_branch` | Create a branch |

**Required env vars:** `GITHUB_TOKEN`, `GITHUB_WEBHOOK_SECRET`

### Jira

| Tool | Description |
|------|-------------|
| `jira.create_ticket` | Create a ticket |
| `jira.update_ticket` | Update ticket fields |
| `jira.get_issue` | Get issue details |

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
| `jenkins.fetch_logs` | Get console output |

**Required env vars:** `JENKINS_URL`, `JENKINS_USER`, `JENKINS_API_TOKEN`

### Gmail

| Tool | Description |
|------|-------------|
| `gmail.read_thread` | Read and summarize a thread |
| `gmail.send_email` | Send an email |

**Required:** `credentials.json` (OAuth client) and completing the OAuth flow to generate `token.json`.

---

## Event System

Events originate from webhooks, Slack commands, and scheduled jobs:

| Event | Source |
|-------|--------|
| `github.pull_request.opened` | GitHub webhook |
| `jira.issue.created` | Jira webhook |
| `jenkins.build.failed` | Jenkins webhook |
| `slack.command.invoked` | Slack command |

Events are stored in PostgreSQL and dispatched to subscribed workflow handlers.

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

### Adding a new workflow

1. Create a `.yaml` file in `workflows/`
2. Set `trigger` to the event type you want to match
3. List the `actions` (tools) to execute in order
4. Restart the agent

---

## Webhook Server

Runs on `http://localhost:8080` by default.

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

## Database (PostgreSQL)

| Table | Contents |
|-------|----------|
| `events` | All incoming events with type, source, payload |
| `workflow_runs` | Workflow execution records with status and results |
| `tool_results` | Inputs and outputs of every tool call |
| `agent_memory` | Persistent agent conversation memory |

Connection configured via `DATABASE_URL` env var. Uses SQLAlchemy + psycopg2.

---

## Security

- All secrets loaded from environment variables / `.env` — never hardcoded.
- Webhook endpoints validate HMAC signatures.
- Logs are filtered to redact tokens and API keys.
- `.env` and credential files are `.gitignore`d.
- Each integration uses minimum required scopes / least privilege tokens.

---

## Testing

```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

130 tests covering: security, database models, event bus, IronClaw client, orchestrator, tool schema registry, all 6 integrations, workflow engine, webhook server, and CLI.

---

## Building the Windows Executable

```bash
pip install pyinstaller
pyinstaller --onefile main.py --name claw-agent
```

Output: `dist/claw-agent.exe`

```bash
claw-agent.exe chat
claw-agent.exe run
claw-agent.exe webhook-server
```

---

## Project Structure

```
ironclaw-developer-agent/
├── agent/
│   ├── orchestrator.py         # Main orchestrator — coordinates IronClaw + tools
│   ├── ironclaw_client.py      # HTTP client for IronClaw runtime
│   ├── planner.py              # Action plan decomposition via IronClaw
│   └── memory.py               # Conversation history with PostgreSQL persistence
├── tools/
│   └── registry.py             # Tool Schema Registry with JSON schema support
├── integrations/
│   ├── slack.py
│   ├── github_integration.py
│   ├── jira_integration.py
│   ├── confluence.py
│   ├── jenkins.py
│   └── gmail.py
├── workflows/
│   ├── engine.py               # Workflow execution engine
│   ├── loader.py               # YAML workflow parser
│   ├── pr_opened.yaml
│   ├── build_failed.yaml
│   └── jira_created.yaml
├── events/
│   ├── bus.py                  # Async event bus with PostgreSQL persistence
│   └── types.py                # Event models and source enum
├── webhooks/
│   └── server.py               # FastAPI webhook endpoints
├── security/
│   └── secrets.py              # Credential loading, redaction, HMAC validation
├── database/
│   ├── postgres.py             # PostgreSQL engine, session, connection management
│   └── models.py               # SQLAlchemy ORM models
├── cli/
│   └── chat.py                 # Interactive chat interface (Rich)
├── config/
│   └── config.yaml
├── tests/                      # 130 tests
├── logs/
├── .env.example
├── .gitignore
├── requirements.txt
├── main.py                     # Entry point and CLI commands
└── README.md
```
