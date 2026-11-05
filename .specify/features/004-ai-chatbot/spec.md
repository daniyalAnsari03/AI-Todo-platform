# Feature Specification: AI Todo Chatbot (Phase III)

**Feature Branch**: `004-ai-chatbot`

**Created**: 2026-10-24

**Status**: implemented and manually verified 2026-10-25.

**Input**: User description: "Phase III (AI Todo Chatbot) must be specified exactly from the official Hackathon PDF Phase III section and must not implement code or migrations yet. The app provides a conversational interface for the five basic task features, uses the mandated stack, and keeps the existing Phase I and Phase II behavior working."

**Source of truth**: The official Hackathon PDF Phase III section, as restated in `docs/fix.txt`; requirements below are derived from that section and are intentionally limited to WHAT the system must do, not HOW it is implemented.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Conversational Task Management (Priority: P1)

A user can manage their todo tasks entirely through a conversational interface in natural language, using the five basic features: add, list, update, delete, and complete. The assistant interprets user intent, invokes task tools through an MCP server, and returns a friendly response without requiring the user to know the underlying task APIs.

**Why this priority**: This feature is the core deliverable of Phase III and the primary PDF requirement: natural-language task management over the existing user-scoped task model.

**Independent Test**: Submit natural-language commands like "Add a task to pay bills" and "Delete the meeting task" to a valid authenticated user session and verify the correct tool invocations and persisted task changes.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they say "Add a task to pay bills", **Then** the system creates a task for that user with the title "Pay bills" and the task remains in the user's task list.
2. **Given** an authenticated user, **When** they ask "List my tasks", **Then** the system returns the current tasks for that user and does not include other users' tasks.
3. **Given** an authenticated user with an existing task, **When** they say "Mark the meeting task complete", **Then** the system marks the matching task complete.
4. **Given** an authenticated user with an existing task, **When** they say "Delete the meeting task", **Then** the system resolves the task, invokes delete_task, and removes it from the user's task list.
5. **Given** an authenticated user with an existing task, **When** they say "Rename the meeting task to Sprint review", **Then** the system invokes update_task with the matching task ID and updates the title.
6. **Given** an authenticated user, **When** they provide an ambiguous or invalid task reference, **Then** the assistant asks for clarification or returns a friendly error instead of exposing stack traces or unrelated data.

---

### User Story 2 - Stateless Request Flow & Conversation Persistence (Priority: P1)

The chat API supports a stateless request lifecycle: each request receives a message, loads conversation history from the database, stores the user message, runs the AI agent with MCP tools, stores the assistant response, and returns the result. The backend keeps no in-memory session state, but conversations can resume across a server restart because the conversation history is stored in the database.

**Why this priority**: The PDF explicitly requires the 9-step stateless request cycle and restart-resume behavior, which is a core functional and operational contract.

**Independent Test**: Restart the backend service after creating a conversation, then submit a follow-up message using the same `conversation_id` and verify the prior history is restored and the agent continues correctly.

**Acceptance Scenarios**:

1. **Given** a valid chat request with a `conversation_id`, **When** the backend receives it, **Then** it loads the matching conversation and prior messages from persistent storage.
2. **Given** a valid chat request without `conversation_id`, **When** the backend receives it, **Then** it creates a new conversation and stores the initial user message.
3. **Given** a completed agent run, **When** the assistant response is stored, **Then** the conversation contains the assistant message and the system returns the response plus the list of MCP tool calls.
4. **Given** a server restart, **When** the user resumes the same conversation, **Then** the message history is still available without any in-memory session state.

---

### User Story 3 - Task Tooling and Data Model (Priority: P1)

The backend exposes stateless, DB-backed tool functions that manipulate the user's tasks. Each tool validates ownership against the verified authenticated user, uses the `user_id` from the validated JWT rather than any model-selected value, and returns the PDF-defined task objects or task list structures.

**Why this priority**: The real system behavior is governed by the tool contracts, required task shapes, and strict user isolation.

**Independent Test**: Call each tool as the authenticated user and verify title/description updates, list filtering, completion toggling, task deletion, and not-found/ownership behavior.

**Acceptance Scenarios**:

1. **Given** an authenticated user, **When** they ask to add a task, **Then** the system calls `add_task(user_id, title, description?)` and the created task matches the task model contract.
2. **Given** an authenticated user with tasks, **When** they ask to list tasks or filtered tasks, **Then** the system calls `list_tasks(user_id, status?)` and returns only that user's tasks in the required shape.
3. **Given** an authenticated user with an existing task, **When** they ask to complete or mark it done, **Then** the task's completion status is updated and the response includes `task_id`, `status`, and `title`.
4. **Given** an authenticated user with an existing task, **When** they ask to update it, **Then** the system calls `update_task(user_id, task_id, title?, description?)` and preserves the task ID and ownership.
5. **Given** an authenticated user with an existing task, **When** they ask to delete it, **Then** the system calls `delete_task(user_id, task_id)` and the task no longer appears in subsequent lists.

---

### User Story 4 - Authenticated Chat Endpoint and User Isolation (Priority: P1)

The chat endpoint is protected by Better Auth JWT verification and follows the same 401/403 authentication policy as Phase II. The `user_id` in the URL must match the verified token subject; user data is isolated by user, and the MCP tools must never receive a user-chosen or model-influenced `user_id` value.

**Why this priority**: Without strict user isolation and authentication, the system would expose other users' tasks or allow data leakage via the model.

**Independent Test**: Invoke the chat endpoint with no token, a valid token for a different user, and a valid token for the same user, and verify the expected status codes and data leakage prevention.

**Acceptance Scenarios**:

1. **Given** no valid JWT, **When** a client calls `POST /api/{user_id}/chat`, **Then** the request fails with HTTP 401 and no chat or task data is exposed.
2. **Given** a valid JWT for user A, **When** user A calls `/api/{user_id}/chat` for user B where A ≠ B, **Then** the request is rejected with HTTP 403 before any DB lookup.
3. **Given** a valid token for user A, **When** the model invokes tools for user A, **Then** the tool calls operate only on tasks owned by user A.
4. **Given** a valid chat message, **When** the response returns, **Then** it includes `conversation_id`, `response`, and `tool_calls` in the required structure.

---

### User Story 5 - Frontend Chat UI and Existing App Safety (Priority: P1)

A ChatKit-based chat interface is added to the existing app without disrupting the current dashboard or authenticated flows. The UI is reachable from the dashboard, authenticated, and uses the backend chat endpoint while preserving the existing dashboard state and behavior.

**Why this priority**: The PDF requires a frontend UI in addition to backend functionality, but the existing dashboard must remain untouched and functional.

**Independent Test**: Open the app as an authenticated user, navigate to the chat interface from the dashboard, and send a message that creates or updates a task.

**Acceptance Scenarios**:

1. **Given** an authenticated user on the dashboard, **When** they open the chat UI, **Then** they can access the chat panel or page without leaving the logged-in session.
2. **Given** a user submits a natural-language command in the chat UI, **When** the message is sent, **Then** the app calls the backend chat endpoint and renders the assistant reply.
3. **Given** the existing dashboard, **When** the chat UI is added, **Then** the dashboard remains intact and the new chat experience is additive rather than replacing or breaking current functionality.

---

### User Story 6 - Error Handling and Security Boundaries (Priority: P1)

The system handles ambiguous, invalid, empty, and upstream failures gracefully. User task text is treated as data, not instructions. Secrets are never logged or embedded in code. The backend and tools enforce strict ownership and reject prompt-injection attempts by never allowing model-selected user IDs or untrusted instructions to modify task scope.

**Why this priority**: The PDF includes explicit security and error-handling requirements that protect user isolation and operational reliability.

**Independent Test**: Trigger malformed requests, empty lists, task-not-found conditions, a model error, and an injection-like task title, and confirm the user sees friendly responses with no stack traces or credentials.

**Acceptance Scenarios**:

1. **Given** a user asks for a task that does not exist, **When** the system tries to resolve it, **Then** it responds with a friendly not-found message and does not leak other users' task data.
2. **Given** an empty or invalid task list state, **When** the assistant tries to list tasks, **Then** it returns a friendly empty-list message without stack traces.
3. **Given** an OpenAI or upstream failure, **When** the agent call fails, **Then** the system returns a safe message to the user and logs no sensitive secrets.
4. **Given** task text containing prompt-like language, **When** it is processed as data, **Then** it is never interpreted as instructions for the scheduler or tool invocation logic.

---

## Requirements *(mandatory)*

### Phase III — Objective and Scope

- **FR-001**: The system MUST provide a conversational interface for all five basic features: add, list, update, delete, and complete tasks using natural language.
- **FR-002**: The Phase III system MUST operate over the existing task model and the authenticated user-scoped task data without altering existing Phase I or II behavior outside the approved scope.
- **FR-003**: The PDF’s Phase III requirements are the governing source of truth for this feature; any conflict between the PDF and local implementation must be resolved in favor of the PDF unless explicitly amended by user decision.

### Phase III — Mandatory Stack (non-substitutable)

- **FR-010**: The frontend MUST use OpenAI ChatKit as the chat interface technology.
- **FR-011**: The backend MUST use FastAPI for the HTTP API.
- **FR-012**: The agent logic MUST use the OpenAI Agents SDK.
- **FR-013**: The system MUST use the Official MCP SDK with an MCP server that exposes task tools to the agent.
- **FR-014**: Persistence MUST use SQLModel and Neon.
- **FR-015**: Auth MUST use Better Auth with JWT enforcement in the backend.
- **FR-016**: No substitutions or alternative stacks are permitted for the Phase III scope; all required components remain present in the implementation.

### Phase III — Data Models and Migration Constraints

- **FR-020**: The existing task model (`todo_item`) remains the task data model in use for task operations.
- **FR-021**: The system MUST add a `Conversation` model with at least: `user_id`, `id`, `created_at`, and `updated_at`.
- **FR-022**: The system MUST add a `Message` model with at least: `user_id`, `id`, `conversation_id`, `role` (`user` or `assistant`), `content`, and `created_at`.
- **FR-023**: The conversation and message tables MUST be created as new tables only; no existing task tables or columns may be altered for the Phase III feature.
- **FR-024**: The data model MUST support conversation continuation across restarts without server-side in-memory session state.

### Phase III — Chat Endpoint Contract

- **FR-030**: The backend MUST expose `POST /api/{user_id}/chat`.
- **FR-031**: The request body MUST include a required `message` string and an optional `conversation_id` integer.
- **FR-032**: When `conversation_id` is absent, the backend MUST create a new conversation for the authenticated user.
- **FR-033**: The response MUST include `conversation_id`, `response`, and `tool_calls` (the list of MCP tools invoked during the request).
- **FR-034**: The chat endpoint MUST enforce the same JWT auth rules as Phase II: missing or invalid tokens return 401; URL `user_id` mismatch with the verified token user returns 403 before any DB lookup.
- **FR-035**: The backend MUST not rely on server-held request state. Each chat request is stateless and reconstructs state from the database.

### Phase III — Stateless Request Cycle

- **FR-040**: The request lifecycle MUST follow the PDF’s nine-step sequence: receive message → fetch history from DB → build message array → store user message → run agent with MCP tools → agent invokes tool(s) → store assistant response → return response → no server-held state.
- **FR-041**: Conversation history MUST persist across server restarts and resume using the stored `conversation_id` and persisted messages.
- **FR-042**: The system MUST behave correctly when the same conversation is resumed after a backend restart.

### Phase III — MCP Tool Contract

- **FR-050**: The agent MUST call stateless, DB-backed MCP tools for task operations: `add_task`, `list_tasks`, `complete_task`, `delete_task`, and `update_task`.
- **FR-051**: `add_task(user_id, title, description?)` MUST create a task for the authenticated user and return the created task or equivalent result object.
- **FR-052**: `list_tasks(user_id, status? all|pending|completed)` MUST list only that user's tasks and return a list of task objects, including the PDF’s task object shape.
- **FR-053**: `complete_task(user_id, task_id)` MUST complete or otherwise update the target task for the authenticated user.
- **FR-054**: `delete_task(user_id, task_id)` MUST delete the task only if it belongs to the authenticated user.
- **FR-055**: `update_task(user_id, task_id, title?, description?)` MUST update the task details for the authenticated user only.
- **FR-056**: Task tool outputs MUST include the PDF-defined return shapes, including `task_id`/`status`/`title` for single-task results and arrays for list results.
- **FR-057**: The user_id passed to each MCP tool MUST be the verified token user_id, never a value chosen by the model.

### Phase III — Agent Behavior and Natural Language Scenarios

- **FR-060**: The agent MUST support the PDF’s required behavior table for task creation, listing, completion, deletion, update, confirmation, and error handling.
- **FR-061**: The agent MUST accept and correctly interpret the PDF’s natural-language examples, including requests like "Delete the meeting task" and "I need to remember to pay bills".
- **FR-062**: When the user references a task ambiguously, the agent MUST request clarification or return a friendly disambiguation message rather than guessing or acting on the wrong task.
- **FR-063**: The agent MUST maintain a task-scoped, user-scoped operational context that never exceeds the authenticated user’s task namespace.

### Phase III — Error Handling and User Experience

- **FR-070**: The system MUST return friendly messages for task not found, empty list states, ambiguous task references, invalid input, and OpenAI/upstream failures.
- **FR-071**: Errors MUST not reveal stack traces or internal implementation details to the user.
- **FR-072**: The backend MUST gracefully handle empty list conditions, invalid task references, and malformed requests without exposing internal states.
- **FR-073**: The frontend and backend MUST present user-safe, non-technical language for failures.

### Phase III — Frontend and Dashboard Integration

- **FR-080**: The frontend MUST add a ChatKit-based chat UI to the existing app, reachable from the `/dashboard` area or equivalent authenticated route.
- **FR-081**: The chat UI MUST be authenticated and must use the existing auth session and token mechanisms without breaking the current dashboard.
- **FR-082**: The existing dashboard behavior and UI MUST remain intact; the new chat UI is additive and must not replace the current app surface.
- **FR-083**: The frontend MUST support the complete task-management conversation flow through the backend chat endpoint.

### Phase III — Deliverables and Documentation

- **FR-090**: The implementation MUST include a frontend ChatKit UI, a backend FastAPI service with Agents SDK and MCP integration, persisted conversation and message storage, migration scripts, and setup instructions.
- **FR-091**: The application MUST document its setup instructions in the repository README and include any required spec and design documentation under `/specs`.
- **FR-092**: Deliverables MUST match the Phase III PDF requirements and be reviewable in the repo.

### Phase III — Security Requirements

- **FR-100**: All task operations MUST be scoped strictly to the authenticated user.
- **FR-101**: The `user_id` passed to MCP tools MUST be the verified token user_id, never a value selected by the model, client code, or prompt text.
- **FR-102**: Task content MUST be treated as data, not instructions; prompt injection or model-supplied instructions MUST never change the task scope or auth context.
- **FR-103**: No secrets may be committed to code, logged, or exposed in error responses.
- **FR-104**: The system MUST use only environment variable names such as `OPENAI_API_KEY` and `NEXT_PUBLIC_OPENAI_DOMAIN_KEY`; actual values are never checked into the repo or printed.
- **FR-105**: The backend MUST enforce the same user verification and authorization boundaries as Phase II; mismatched `user_id`s and invalid JWTs are rejected before task actions are executed.

### Phase III — Out of Scope

- **FR-110**: Intermediate and advanced features are out of scope, including priorities, tags, search, due dates, recurring tasks, and related task management features.
- **FR-111**: Kubernetes, Kafka, Dapr, and Urdu/voice features are explicitly out of scope.

### Phase III — Acceptance Criteria (cross-cutting)

- **AC-001**: Given an authenticated user and a new message, When the chat request is sent, Then a conversation is created or resumed and the response includes the assistant output and tool call list.
- **AC-002**: Given a restart, When the conversation is resumed, Then history is still available from the database and the app works without in-memory session state.
- **AC-003**: Given a valid JWT, When the chat route is called for the same user, Then the request succeeds and all tools operate within the user’s own task namespace.
- **AC-004**: Given a path `user_id` mismatch, When the request is processed, Then the request is rejected with 403 before any DB lookup.
- **AC-005**: Given a valid tool call with a missing task, When the tool is invoked, Then the system returns a friendly error and no unrelated task data is exposed.
- **AC-006**: Given natural-language examples from the PDF, When the agent interprets them, Then the correct task operation is executed and the user receives the expected assistant reply.
- **AC-007**: Given an invalid or empty request, When the message is malformed or blank, Then the system rejects it gracefully with a friendly message.
- **AC-008**: Given an upstream OpenAI failure, When the agent call fails, Then the system returns a safe user-facing response without stack traces.

## Open Questions / PDF Ambiguities

### OQ-A — Hosted ChatKit vs. ChatKit pointed at our own FastAPI backend
- **PDF reference**: Phase III section describes a ChatKit frontend and a stateless `/api/{user_id}/chat` endpoint; it also references domain allowlisting and a domain key.
- **Options**:
  1. Host ChatKit through OpenAI’s provided hosted flow with a domain allowlist and domain key.
  2. Point ChatKit to our own FastAPI backend service for chat requests.
- **Recommendation**: Treat both as valid deployment patterns but explicitly confirm the chosen integration model before implementation; the PDF requires a stateless backend endpoint, so a backend-first integration is the safer default unless the host configuration is explicitly approved.
- **Decision (approved by user, 2026-10-24)**: ChatKit: The PDF contract POST /api/{user_id}/chat (own stateless endpoint, DB persistence, JWT Bearer) stays primary. The ChatKit UI connects to our own FastAPI backend and sends the JWT Bearer. ChatKit's own protocol may differ from the PDF's simple {conversation_id, message} JSON, so the exact integration (adapter vs. ChatKit protocol) is DEFERRED to the Plan stage, to be decided after reading the current ChatKit docs. The hosted domain allowlist / NEXT_PUBLIC_OPENAI_DOMAIN_KEY applies only to production deployment and is not required for localhost.

### OQ-B — How `user_id` reaches MCP tools securely
- **PDF reference**: MCP tool signatures explicitly include `user_id` as a parameter.
- **Options**:
  1. The backend injects the verified token user_id into each tool call.
  2. The model chooses a user_id value and the backend validates it before execution.
- **Recommendation**: Require backend injection of the verified token user ID and reject any model-supplied user_id value before tool execution; this preserves the user-isolation requirement and avoids a privacy and authorization bug.
- **Decision (approved by user, 2026-10-24)**: user_id: The server injects the verified token user_id into every tool call. The model must never choose user_id. Tool signatures stay as in the PDF; any user_id mismatch is rejected.

### OQ-C — MCP server transport and hosting
- **PDF reference**: “Official MCP SDK” and task tools are required, but transport/hosting is not specified.
- **Options**:
  1. In-process MCP server within the FastAPI process.
  2. Separate-process or remote MCP server for task tools.
- **Recommendation**: Prefer the simplest in-process deployment for the approved scope unless existing infra or team constraints require a remote service; the PDF only requires correct tool semantics, not a distributed deployment model.
- **Decision (approved by user, 2026-10-24)**: MCP hosting: Lives in the same repo and backend, with no extra public port. The exact mechanism (in-process vs. stdio) is DEFERRED to the Plan stage after reading the Official MCP SDK docs.

### OQ-D — Malformed `list_tasks` example and required `user_id`
- **PDF reference**: The list_tasks example appears to include a `user_id` inside the example input even though the PDF also states `user_id` is part of the tool signature.
- **Options**:
  1. `user_id` is required in all tool calls.
  2. `user_id` is omitted from examples but still required externally.
- **Recommendation**: Treat `user_id` as a required parameter in the tool contract because the security and per-user scoping requirements depend on it; the example is likely malformed and should be clarified before implementation.
- **Decision (approved by user, 2026-10-24)**: list_tasks: user_id is REQUIRED (the PDF example is malformed).

### OQ-E — Model choice and API key provisioning
- **PDF reference**: The stack requires OpenAI Agents SDK and ChatKit, but the specific model and provisioning method are not specified.
- **Options**:
  1. Use a production model approved by the team and provision the key in the environment.
  2. Use a smaller fallback model for development and a separate production model for deployment.
- **Recommendation**: Confirm the target model and environment provisioning early; the implementation must only use environment variable names and never commit the actual secret values.
- **Decision (approved by user, 2026-10-24)**: Model/key: The model is configurable via the OPENAI_MODEL env var; the default is DEFERRED to the Plan stage based on current availability. OPENAI_API_KEY lives only in the backend .env, never in the frontend, never logged.

### OQ-F — Existing nullable columns in `todo_item`
- **PDF reference**: The existing `todo_item` model may have nullable `title` or timestamp fields, which affect the migration and tool assumptions.
- **Options**:
  1. Treat nulls as invalid and normalize them at the migration boundary.
  2. Accept nulls temporarily in the tool layer while the migration prepares the data.
- **Recommendation**: Require a documented data normalization strategy before implementation; null or missing values must not silently violate the task model or the PDF contract.
- **Decision (approved by user, 2026-10-24)**: Nullable columns: No schema change in Phase III. Tools must safely handle null title/created_at/updated_at. Schema cleanup remains a separate follow-up.

### OQ-G — Conflict with Amendment 1 (JWKS instead of shared secret)
- **PDF reference**: The Phase II PDF describes shared-secret JWT verification, while the repo’s Amendment 1 explicitly requires JWKS verification for Better Auth JWT plugin compatibility.
- **Options**:
  1. Follow the PDF literally and use a shared secret model.
  2. Follow the repo’s approved Amendment 1 and use JWKS verification with RS256.
- **Recommendation**: Follow the approved Amendment 1 as the governing implementation path for the backend. The stated security goals remain the same; the mechanism is asymmetric JWKS verification instead of a literal shared-secret check.
- **Decision (approved by user, 2026-10-24)**: Amendment 1: The chat endpoint reuses the same JWKS verification as Phase II. No new conflict with the PDF.

## Release Notes / Scope Guard

This specification is limited to Phase III and covers the required conversational interface, mandated stack, user-scoped task tool contracts, persistence requirements, and acceptance criteria.

## Implementation deviations from the PDF

- `conversation` includes an additional nullable `chat_thread_id` column to map persisted conversations to ChatKit thread IDs; the existing `todo_item` schema is unchanged.
- A ChatKit protocol adapter is available at `POST /api/{user_id}/chatkit` in addition to the PDF's canonical `POST /api/{user_id}/chat` endpoint. The PDF endpoint remains independently supported and returns `tool_calls`.
- PostgreSQL URLs are normalized to use the `psycopg2` driver.
- The OpenAI model is configurable with the `OPENAI_MODEL` environment variable.

These implementation details preserve the PDF's required task behavior and user isolation. Production ChatKit hosting may require `NEXT_PUBLIC_OPENAI_DOMAIN_KEY`; local development does not.
