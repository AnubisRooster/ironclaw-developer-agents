# Graph Report - ironclaw-developer-agents  (2026-10-19)

## Corpus Check
- 59 files · ~75,230 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 5 file(s) not represented in the graph (top: (none) 2, .example 1, .jsonl 1)

## Summary
- 595 nodes · 1208 edges · 35 communities (14 shown, 21 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 154 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- get_secrets()
- test_workflows.py
- IronClawClient
- ToolSchemaRegistry
- AgentEvent
- graphify_pipeline.py
- ConversationMemory
- test_integrations.py
- test_agent.py
- confluence.py
- test_database.py
- GitHubIntegration
- JiraIntegration
- main.py
- test_cli_main.py
- SlackIntegration
- redact()
- TestJenkinsIntegration
- cli()
- postgres.py
- orchestrator.py
- AgentMemory
- JenkinsIntegration

## God Nodes (most connected - your core abstractions)
1. `AgentEvent` - 35 edges
2. `ToolSchemaRegistry` - 34 edges
3. `get_secrets()` - 32 edges
4. `ConversationMemory` - 26 edges
5. `IronClawClient` - 20 edges
6. `EventBus` - 18 edges
7. `Orchestrator` - 17 edges
8. `WorkflowEngine` - 17 edges
9. `_build_orchestrator()` - 16 edges
10. `GmailIntegration` - 15 edges

## Surprising Connections (you probably didn't know these)
- `ConversationMemory` --uses--> `AgentMemory`  [INFERRED]
  agent/memory.py → database/models.py
- `Orchestrator` --uses--> `ToolResult`  [INFERRED]
  agent/orchestrator.py → database/models.py
- `Orchestrator` --uses--> `ToolSchemaRegistry`  [INFERRED]
  agent/orchestrator.py → tools/registry.py
- `EventBus` --uses--> `Event`  [INFERRED]
  events/bus.py → database/models.py
- `WorkflowEngine` --uses--> `WorkflowRun`  [INFERRED]
  workflows/engine.py → database/models.py

## Import Cycles
- None detected.

## Communities (35 total, 21 thin omitted)

### Community 0 - "get_secrets()"
Cohesion: 0.06
Nodes (17): EventSource, AppSecrets, get_secrets(), verify_webhook_signature(), TestAppSecrets, TestVerifyWebhookSignature, client(), TestGitHubWebhook (+9 more)

### Community 1 - "test_workflows.py"
Cohesion: 0.08
Nodes (10): TestLoadAllWorkflows, TestLoadWorkflow, TestWorkflowAction, TestWorkflowDefinition, TestWorkflowEngine, WorkflowEngine, load_all_workflows(), load_workflow() (+2 more)

### Community 2 - "IronClawClient"
Cohesion: 0.09
Nodes (4): IronClawClient, Orchestrator, TestIronClawClient, TestOrchestrator

### Community 3 - "ToolSchemaRegistry"
Cohesion: 0.10
Nodes (5): TestToolSchema, TestToolSchemaRegistry, RegisteredTool, ToolSchema, ToolSchemaRegistry

### Community 4 - "AgentEvent"
Cohesion: 0.12
Nodes (4): EventBus, AgentEvent, TestAgentEvent, TestEventBus

### Community 5 - "graphify_pipeline.py"
Cohesion: 0.08
Nodes (3): env_secrets(), _reset_db_singletons(), _reset_secrets_cache()

### Community 8 - "test_agent.py"
Cohesion: 0.16
Nodes (5): ActionPlan, Planner, PlanStep, TestPlanModels, TestPlanner

### Community 9 - "confluence.py"
Cohesion: 0.12
Nodes (3): ConfluenceIntegration, _strip_html(), TestConfluenceIntegration

### Community 10 - "test_database.py"
Cohesion: 0.16
Nodes (8): Base, Event, ToolResult, WorkflowRun, db_session(), TestEventModel, TestToolResultModel, TestWorkflowRunModel

### Community 13 - "main.py"
Cohesion: 0.18
Nodes (5): _build_orchestrator(), chat(), run(), _setup_workflow_engine(), webhook_server()

### Community 15 - "test_cli_main.py"
Cohesion: 0.15
Nodes (4): _chat_loop(), _print_banner(), start_chat(), TestCLIChat

### Community 17 - "redact()"
Cohesion: 0.20
Nodes (4): redact(), RedactingFilter, TestRedact, TestRedactingFilter

### Community 20 - "cli()"
Cohesion: 0.18
Nodes (3): cli(), _setup_logging(), TestMainCLI

### Community 21 - "postgres.py"
Cohesion: 0.20
Nodes (3): check_connection(), get_engine(), get_session_factory()

## Knowledge Gaps
- **21 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `ToolSchemaRegistry` connect `ToolSchemaRegistry` to `test_workflows.py`, `IronClawClient`, `main.py`, `typing`, `orchestrator.py`?**
  _High betweenness centrality (0.126) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `AgentEvent` (e.g. with `EventBus` and `TestAgentEvent`) actually correct?**
  _`AgentEvent` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `get_secrets()` be split into smaller, more focused modules?**
  _Cohesion score 0.06110102843315184 - nodes in this community are weakly interconnected._
- **Why does `get_secrets()` connect `get_secrets()` to `IronClawClient`, `graphify_pipeline.py`, `test_integrations.py`, `confluence.py`, `GitHubIntegration`, `JiraIntegration`, `main.py`, `typing`, `SlackIntegration`, `logging`, `postgres.py`, `JenkinsIntegration`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `ToolSchemaRegistry` (e.g. with `Orchestrator` and `TestToolSchemaRegistry`) actually correct?**
  _`ToolSchemaRegistry` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Should `test_workflows.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07568027210884354 - nodes in this community are weakly interconnected._
- **Why does `Orchestrator` connect `IronClawClient` to `ToolSchemaRegistry`, `ConversationMemory`, `test_agent.py`, `test_database.py`, `main.py`, `orchestrator.py`?**
  _High betweenness centrality (0.092) - this node is a cross-community bridge._