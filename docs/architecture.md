# Claw Agent — Architecture Diagrams

## System Architecture

```mermaid
graph TB
    subgraph External Services
        SLACK["Slack"]
        GITHUB["GitHub"]
        JIRA["Jira"]
        CONFLUENCE["Confluence"]
        JENKINS["Jenkins"]
        GMAIL["Gmail"]
        LLM_API["LLM Provider<br/>(OpenRouter / OpenAI / Ollama)"]
    end

    subgraph Claw Agent
        subgraph Entry Points
            CLI["CLI Chat<br/><i>cli/chat.py</i>"]
            WEBHOOK["Webhook Server<br/><i>webhooks/server.py</i><br/>localhost:8080"]
        end

        subgraph Agent Core
            ORCH["Orchestrator<br/><i>agent/orchestrator.py</i>"]
            PLANNER["Planner<br/><i>agent/planner.py</i>"]
            MEMORY["Conversation Memory<br/><i>agent/memory.py</i>"]
            LLM_CLIENT["LLM Client<br/><i>agent/orchestrator.py</i>"]
            TOOL_REG["Tool Registry<br/><i>agent/orchestrator.py</i>"]
        end

        subgraph Event System
            BUS["Event Bus<br/><i>events/bus.py</i>"]
            TYPES["Event Types<br/><i>events/types.py</i>"]
        end

        subgraph Workflow System
            ENGINE["Workflow Engine<br/><i>workflows/engine.py</i>"]
            LOADER["YAML Loader<br/><i>workflows/loader.py</i>"]
            WF_YAML["Workflow Definitions<br/><i>*.yaml</i>"]
        end

        subgraph Integration Connectors
            I_SLACK["Slack Connector<br/><i>integrations/slack.py</i>"]
            I_GITHUB["GitHub Connector<br/><i>integrations/github_integration.py</i>"]
            I_JIRA["Jira Connector<br/><i>integrations/jira_integration.py</i>"]
            I_CONF["Confluence Connector<br/><i>integrations/confluence.py</i>"]
            I_JENKINS["Jenkins Connector<br/><i>integrations/jenkins.py</i>"]
            I_GMAIL["Gmail Connector<br/><i>integrations/gmail.py</i>"]
        end

        subgraph Infrastructure
            SECRETS["Secure Credentials<br/><i>security/secrets.py</i>"]
            DB["SQLite Database<br/><i>database/models.py</i>"]
        end
    end

    %% User entry
    USER((Developer)) -->|natural language| CLI
    SLACK -->|webhooks| WEBHOOK
    GITHUB -->|webhooks| WEBHOOK
    JIRA -->|webhooks| WEBHOOK
    JENKINS -->|webhooks| WEBHOOK

    %% CLI to Orchestrator
    CLI --> ORCH
    ORCH --> MEMORY
    ORCH --> PLANNER
    ORCH --> LLM_CLIENT
    ORCH --> TOOL_REG
    LLM_CLIENT -->|API calls| LLM_API

    %% Webhook to Event Bus
    WEBHOOK --> BUS
    BUS --> ENGINE
    ENGINE --> LOADER
    LOADER --> WF_YAML

    %% Tool Registry to Connectors
    TOOL_REG --> I_SLACK
    TOOL_REG --> I_GITHUB
    TOOL_REG --> I_JIRA
    TOOL_REG --> I_CONF
    TOOL_REG --> I_JENKINS
    TOOL_REG --> I_GMAIL

    %% Connectors to External
    I_SLACK --> SLACK
    I_GITHUB --> GITHUB
    I_JIRA --> JIRA
    I_CONF --> CONFLUENCE
    I_JENKINS --> JENKINS
    I_GMAIL --> GMAIL

    %% Infrastructure
    SECRETS -.->|credentials| I_SLACK
    SECRETS -.->|credentials| I_GITHUB
    SECRETS -.->|credentials| I_JIRA
    SECRETS -.->|credentials| I_CONF
    SECRETS -.->|credentials| I_JENKINS
    SECRETS -.->|credentials| I_GMAIL
    SECRETS -.->|api key| LLM_CLIENT
    BUS -->|persist events| DB
    ENGINE -->|persist runs| DB
    ORCH -->|persist tool outputs| DB

    %% Styling
    classDef external fill:#e8f4fd,stroke:#2196F3,stroke-width:2px
    classDef entry fill:#fff3e0,stroke:#FF9800,stroke-width:2px
    classDef core fill:#e8f5e9,stroke:#4CAF50,stroke-width:2px
    classDef event fill:#f3e5f5,stroke:#9C27B0,stroke-width:2px
    classDef workflow fill:#fce4ec,stroke:#E91E63,stroke-width:2px
    classDef connector fill:#e0f2f1,stroke:#009688,stroke-width:2px
    classDef infra fill:#f5f5f5,stroke:#607D8B,stroke-width:2px

    class SLACK,GITHUB,JIRA,CONFLUENCE,JENKINS,GMAIL,LLM_API external
    class CLI,WEBHOOK entry
    class ORCH,PLANNER,MEMORY,LLM_CLIENT,TOOL_REG core
    class BUS,TYPES event
    class ENGINE,LOADER,WF_YAML workflow
    class I_SLACK,I_GITHUB,I_JIRA,I_CONF,I_JENKINS,I_GMAIL connector
    class SECRETS,DB infra
```

## Data Flow — Chat Request

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant CLI as CLI Chat
    participant Orch as Orchestrator
    participant Mem as Memory
    participant LLM as LLM Client
    participant API as LLM Provider
    participant Reg as Tool Registry
    participant Tool as Integration<br/>Connector
    participant DB as SQLite

    Dev->>CLI: "Summarize PR 456 in org/repo"
    CLI->>Orch: handle_message(user_input)
    Orch->>Mem: add_message("user", input)
    Orch->>Mem: to_llm_messages()
    Mem-->>Orch: conversation history

    Orch->>LLM: chat(system_prompt + history)
    LLM->>API: POST /chat/completions
    API-->>LLM: response with tool_call block
    LLM-->>Orch: "```tool_call {tool_name: github.summarize_pull_request, ...}```"

    Orch->>Orch: parse tool_call JSON
    Orch->>Reg: get_tool("github.summarize_pull_request")
    Reg-->>Orch: GitHubIntegration.summarize_pull_request
    Orch->>Tool: summarize_pull_request(repo, pr_number)
    Tool-->>Orch: {title, body, changed_files, ...}
    Orch->>DB: store ToolOutput

    Orch->>Mem: add_message("user", "[Tool result]")
    Orch->>LLM: chat(updated history with tool result)
    LLM->>API: POST /chat/completions
    API-->>LLM: natural language summary
    LLM-->>Orch: "PR 456 adds feature X..."

    Orch->>Mem: add_message("assistant", response)
    Orch-->>CLI: "PR 456 adds feature X..."
    CLI-->>Dev: display formatted response
```

## Data Flow — Webhook Event (PR Opened)

```mermaid
sequenceDiagram
    participant GH as GitHub
    participant WH as Webhook Server<br/>POST /webhooks/github
    participant Sec as Signature<br/>Validation
    participant Bus as Event Bus
    participant DB as SQLite
    participant Eng as Workflow Engine
    participant YAML as pr_opened.yaml
    participant GH_C as GitHub Connector
    participant SL_C as Slack Connector
    participant JR_C as Jira Connector

    GH->>WH: POST /webhooks/github<br/>{action: opened, pull_request: {...}}
    WH->>Sec: verify HMAC signature
    Sec-->>WH: valid ✓

    WH->>WH: build AgentEvent<br/>type: github.pull_request.opened
    WH->>Bus: publish(event)
    Bus->>DB: persist event row

    Bus->>Eng: dispatch to subscribed handler
    Eng->>YAML: match trigger → pr_opened_workflow

    Note over Eng: Step 1/3
    Eng->>GH_C: github.summarize_pull_request()
    GH_C-->>Eng: {title, body, additions, deletions}

    Note over Eng: Step 2/3
    Eng->>SL_C: slack.send_message(#dev-notifications)
    SL_C-->>Eng: {ok: true, ts: ...}

    Note over Eng: Step 3/3
    Eng->>JR_C: jira.link_github_issue()
    JR_C-->>Eng: {linked: true}

    Eng->>DB: persist WorkflowRun<br/>status: completed
```

## Data Flow — Build Failed Workflow

```mermaid
sequenceDiagram
    participant JK as Jenkins
    participant WH as Webhook Server<br/>POST /webhooks/jenkins
    participant Bus as Event Bus
    participant Eng as Workflow Engine
    participant JK_C as Jenkins Connector
    participant LLM as LLM Client
    participant SL_C as Slack Connector
    participant DB as SQLite

    JK->>WH: POST /webhooks/jenkins<br/>{build: {status: failure}}
    WH->>Bus: publish(jenkins.build.failed)
    Bus->>DB: persist event

    Bus->>Eng: dispatch → build_failed_workflow

    Note over Eng: Step 1/3
    Eng->>JK_C: jenkins.fetch_build_logs()
    JK_C-->>Eng: {log_tail: "ERROR at line 42..."}

    Note over Eng: Step 2/3
    Eng->>LLM: agent.summarize(log content)
    LLM-->>Eng: "Build failed due to null pointer in AuthService"

    Note over Eng: Step 3/3
    Eng->>SL_C: slack.send_message(#build-alerts)
    SL_C-->>Eng: {ok: true}

    Eng->>DB: persist WorkflowRun
```

## Data Flow — Jira Issue Created Workflow

```mermaid
sequenceDiagram
    participant JR as Jira
    participant WH as Webhook Server<br/>POST /webhooks/jira
    participant Bus as Event Bus
    participant Eng as Workflow Engine
    participant GH_C as GitHub Connector
    participant SL_C as Slack Connector
    participant JR_C as Jira Connector
    participant DB as SQLite

    JR->>WH: POST /webhooks/jira<br/>{webhookEvent: jira:issue_created}
    WH->>Bus: publish(jira.issue.created)
    Bus->>DB: persist event

    Bus->>Eng: dispatch → jira_created_workflow

    Note over Eng: Step 1/3
    Eng->>GH_C: github.create_issue()
    GH_C-->>Eng: {number: 42, url: "..."}

    Note over Eng: Step 2/3
    Eng->>SL_C: slack.send_message(#dev-team)
    SL_C-->>Eng: {ok: true}

    Note over Eng: Step 3/3
    Eng->>JR_C: jira.update_ticket(github_link)
    JR_C-->>Eng: {updated: true}

    Eng->>DB: persist WorkflowRun
```

## Component Dependency Map

```mermaid
graph LR
    subgraph "Depends on nothing"
        SECRETS["security/secrets"]
        TYPES["events/types"]
    end

    subgraph "Depends on secrets"
        DB["database/models"]
        I_SL["integrations/slack"]
        I_GH["integrations/github"]
        I_JR["integrations/jira"]
        I_CO["integrations/confluence"]
        I_JK["integrations/jenkins"]
        I_GM["integrations/gmail"]
        LLM["LLMClient"]
    end

    subgraph "Depends on events + DB"
        BUS["events/bus"]
    end

    subgraph "Depends on LLM"
        MEM["agent/memory"]
        PLAN["agent/planner"]
    end

    subgraph "Depends on bus + loader"
        LOADER["workflows/loader"]
        ENGINE["workflows/engine"]
    end

    subgraph "Depends on bus + secrets"
        WEBHOOK["webhooks/server"]
    end

    subgraph "Top-level orchestration"
        ORCH["agent/orchestrator"]
        MAIN["main.py"]
        CLI_MOD["cli/chat"]
    end

    SECRETS --> DB
    SECRETS --> I_SL & I_GH & I_JR & I_CO & I_JK & I_GM
    SECRETS --> LLM
    SECRETS --> WEBHOOK
    TYPES --> BUS
    DB --> BUS
    DB --> ENGINE
    DB --> ORCH
    LLM --> PLAN
    LLM --> ORCH
    MEM --> ORCH
    PLAN --> ORCH
    BUS --> ENGINE
    BUS --> WEBHOOK
    LOADER --> ENGINE
    ORCH --> CLI_MOD
    ORCH --> MAIN
    ENGINE --> MAIN
    WEBHOOK --> MAIN
    CLI_MOD --> MAIN
```
