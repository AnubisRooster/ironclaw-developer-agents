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
    end

    subgraph IronClaw Runtime
        IC["IronClaw<br/>(Rust OpenClaw)"]
        LLM_API["LLM Provider"]
        IC -->|reasoning| LLM_API
    end

    subgraph Claw Agent
        subgraph Entry Points
            CLI["CLI Chat<br/><i>cli/chat.py</i>"]
            WEBHOOK["Webhook Server<br/><i>webhooks/server.py</i><br/>localhost:8080"]
        end

        subgraph Agent Core
            ORCH["Orchestrator<br/><i>agent/orchestrator.py</i>"]
            IC_CLIENT["IronClaw Client<br/><i>agent/ironclaw_client.py</i>"]
            PLANNER["Planner<br/><i>agent/planner.py</i>"]
            MEMORY["Conversation Memory<br/><i>agent/memory.py</i>"]
        end

        subgraph Tool Layer
            TOOL_REG["Tool Schema Registry<br/><i>tools/registry.py</i>"]
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
            DB["PostgreSQL<br/><i>database/postgres.py</i>"]
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
    ORCH --> IC_CLIENT
    ORCH --> TOOL_REG
    IC_CLIENT -->|HTTP/JSON| IC

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
    SECRETS -.->|api key| IC_CLIENT
    BUS -->|persist events| DB
    ENGINE -->|persist runs| DB
    ORCH -->|persist tool results| DB
    MEMORY -.->|persist memory| DB

    %% Styling
    classDef external fill:#e8f4fd,stroke:#2196F3,stroke-width:2px
    classDef ironclaw fill:#fff9c4,stroke:#FFC107,stroke-width:2px
    classDef entry fill:#fff3e0,stroke:#FF9800,stroke-width:2px
    classDef core fill:#e8f5e9,stroke:#4CAF50,stroke-width:2px
    classDef tool fill:#e3f2fd,stroke:#1976D2,stroke-width:2px
    classDef event fill:#f3e5f5,stroke:#9C27B0,stroke-width:2px
    classDef workflow fill:#fce4ec,stroke:#E91E63,stroke-width:2px
    classDef connector fill:#e0f2f1,stroke:#009688,stroke-width:2px
    classDef infra fill:#f5f5f5,stroke:#607D8B,stroke-width:2px

    class SLACK,GITHUB,JIRA,CONFLUENCE,JENKINS,GMAIL external
    class IC,LLM_API ironclaw
    class CLI,WEBHOOK entry
    class ORCH,IC_CLIENT,PLANNER,MEMORY core
    class TOOL_REG tool
    class BUS,TYPES event
    class ENGINE,LOADER,WF_YAML workflow
    class I_SLACK,I_GITHUB,I_JIRA,I_CONF,I_JENKINS,I_GMAIL connector
    class SECRETS,DB infra
```

## Data Flow — Chat Request via IronClaw

```mermaid
sequenceDiagram
    actor Dev as Developer
    participant CLI as CLI Chat
    participant Orch as Orchestrator
    participant Mem as Memory
    participant IC as IronClaw Client
    participant Runtime as IronClaw Runtime
    participant Reg as Tool Schema Registry
    participant Tool as Integration<br/>Connector
    participant DB as PostgreSQL

    Dev->>CLI: "Summarize PR 456 in org/repo"
    CLI->>Orch: handle_message(user_input)
    Orch->>Mem: add_message("user", input)
    Orch->>Reg: get_all_tools()
    Reg-->>Orch: [tool schemas with JSON params]
    Orch->>Mem: to_llm_messages()
    Mem-->>Orch: conversation history

    Orch->>IC: chat(messages, tools)
    IC->>Runtime: POST /v1/chat
    Runtime-->>IC: {actions: [{tool: "github.summarize_pr", parameters: {...}}]}
    IC-->>Orch: response with actions

    Orch->>Reg: execute_tool("github.summarize_pr", params)
    Reg->>Tool: summarize_pull_request(repo, pr_number)
    Tool-->>Reg: {title, body, changed_files, ...}
    Reg-->>Orch: tool result
    Orch->>DB: store ToolResult

    Orch->>Mem: add_message("user", "[Tool result]")
    Orch->>IC: chat(updated messages, tools)
    IC->>Runtime: POST /v1/chat
    Runtime-->>IC: {content: "PR 456 adds feature X..."}
    IC-->>Orch: text response

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
    participant DB as PostgreSQL
    participant Eng as Workflow Engine
    participant YAML as pr_opened.yaml
    participant Reg as Tool Schema Registry
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
    Eng->>Reg: execute_tool(github.summarize_pull_request)
    Reg->>GH_C: summarize_pull_request()
    GH_C-->>Reg: {title, body, additions, deletions}
    Reg-->>Eng: result

    Note over Eng: Step 2/3
    Eng->>Reg: execute_tool(slack.send_message)
    Reg->>SL_C: send_message(#dev-notifications)
    SL_C-->>Reg: {ok: true, ts: ...}
    Reg-->>Eng: result

    Note over Eng: Step 3/3
    Eng->>Reg: execute_tool(jira.link_github_issue)
    Reg->>JR_C: link_github_issue()
    JR_C-->>Reg: {linked: true}
    Reg-->>Eng: result

    Eng->>DB: persist WorkflowRun<br/>status: completed
```

## Data Flow — Build Failed Workflow

```mermaid
sequenceDiagram
    participant JK as Jenkins
    participant WH as Webhook Server<br/>POST /webhooks/jenkins
    participant Bus as Event Bus
    participant Eng as Workflow Engine
    participant Reg as Tool Schema Registry
    participant JK_C as Jenkins Connector
    participant IC as IronClaw Client
    participant Runtime as IronClaw Runtime
    participant SL_C as Slack Connector
    participant DB as PostgreSQL

    JK->>WH: POST /webhooks/jenkins<br/>{build: {status: failure}}
    WH->>Bus: publish(jenkins.build.failed)
    Bus->>DB: persist event

    Bus->>Eng: dispatch → build_failed_workflow

    Note over Eng: Step 1/3
    Eng->>Reg: execute_tool(jenkins.fetch_build_logs)
    Reg->>JK_C: fetch_build_logs()
    JK_C-->>Reg: {log_tail: "ERROR at line 42..."}
    Reg-->>Eng: result

    Note over Eng: Step 2/3
    Eng->>Reg: execute_tool(agent.summarize)
    Reg->>IC: summarize(log content)
    IC->>Runtime: POST /v1/summarize
    Runtime-->>IC: "Build failed due to null pointer in AuthService"
    IC-->>Reg: summary
    Reg-->>Eng: result

    Note over Eng: Step 3/3
    Eng->>Reg: execute_tool(slack.send_message)
    Reg->>SL_C: send_message(#build-alerts)
    SL_C-->>Reg: {ok: true}
    Reg-->>Eng: result

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
        DB["database/postgres"]
        I_SL["integrations/slack"]
        I_GH["integrations/github"]
        I_JR["integrations/jira"]
        I_CO["integrations/confluence"]
        I_JK["integrations/jenkins"]
        I_GM["integrations/gmail"]
        IC["agent/ironclaw_client"]
    end

    subgraph "Standalone"
        TOOL_REG["tools/registry"]
        MODELS["database/models"]
    end

    subgraph "Depends on events + DB"
        BUS["events/bus"]
    end

    subgraph "Depends on IronClaw"
        MEM["agent/memory"]
        PLAN["agent/planner"]
    end

    subgraph "Depends on bus + loader + registry"
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
    SECRETS --> IC
    SECRETS --> WEBHOOK
    TYPES --> BUS
    MODELS --> DB
    DB --> BUS
    DB --> ENGINE
    DB --> ORCH
    IC --> PLAN
    IC --> ORCH
    MEM --> ORCH
    PLAN --> ORCH
    TOOL_REG --> ORCH
    TOOL_REG --> ENGINE
    BUS --> ENGINE
    BUS --> WEBHOOK
    LOADER --> ENGINE
    ORCH --> CLI_MOD
    ORCH --> MAIN
    ENGINE --> MAIN
    WEBHOOK --> MAIN
    CLI_MOD --> MAIN
```
