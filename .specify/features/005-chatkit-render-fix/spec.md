# Feature Specification: ChatKit Rendering and Adapter Repair

**Feature Branch**: `005-chatkit-render-fix`

**Created**: 2026-10-25

**Status**: Approved by user on 2026-10-25; amendment approved on 2026-10-25

**Input**: `docs/fix.txt` and the user's request to implement it.

## User Scenarios & Testing

### User Story 1 - See and use the chat interface (Priority: P1)

An authenticated user opening `/chat` can see the ChatKit interface or a concise,
actionable status explaining why it is not available.

**Independent Test**: Render the chat page with successful, pending, and failed
token requests and ChatKit errors; verify the widget or status is visible without
exposing a token.

**Acceptance Scenarios**:

1. **Given** a valid user ID and successful token retrieval, **When** `/chat`
   loads, **Then** ChatKit renders and the status indicates the user ID is
   present and the token is ready.
2. **Given** token retrieval is pending or fails, **When** `/chat` loads,
   **Then** a visible status reports loading or a short error and never displays
   the token.
3. **Given** ChatKit reports an error, **When** it occurs, **Then** the visible
   status includes its message without hiding other status information.

### User Story 2 - Use ChatKit protocol operations (Priority: P1)

The ChatKit adapter accepts the protocol operations required to create and
retrieve a thread and its items, returning valid HTTP responses and content
types without real OpenAI calls or database writes in tests.

**Independent Test**: Use the FastAPI test client with mocked ChatKit/OpenAI
behavior and isolated test storage to POST `threads.create`, `threads.list`,
`items.list`, and `threads.get_by_id`.

**Acceptance Scenarios**:

1. **Given** an authenticated test user, **When** each of the four operations is
   posted to `/api/{user_id}/chatkit`, **Then** it returns a valid successful
   response with the expected protocol content type and response shape.
2. **Given** an adapter response error, **When** a test operation is processed,
   **Then** the adapter reports the failure rather than returning an empty or
   success-shaped fallback.

## Requirements

### Functional Requirements

- **FR-001**: The `/chat` page MUST render ChatKit after successful token
  retrieval and MUST expose token loading and failure states visibly.
- **FR-002**: A status line under the page heading MUST report whether the user
  ID is present, whether the token is loading, ready, or in error, and any
  ChatKit `onError` message; it MUST NOT reveal the token.
- **FR-003**: The frontend MUST continue using the authenticated token for
  ChatKit requests and the existing same-origin route to the backend.
- **FR-004**: Automated backend tests MUST cover `threads.create`,
  `threads.list`, `items.list`, and `threads.get_by_id` through the FastAPI test
  client, with external AI behavior mocked and no real database writes.
- **FR-005**: The adapter MUST return valid operation-specific response bodies
  and content types, including streaming responses where required, and MUST
  surface adapter errors instead of silently producing empty responses.
- **FR-006**: The fix MUST NOT change todo-item behavior, auth configuration, or
  dashboard behavior.
- **FR-007**: Validation MUST include the full frontend test suite, frontend
  production build, and full backend test suite.

## Edge Cases

- Token retrieval fails, returns an invalid response, or is still pending.
- ChatKit reports an error after initialization.
- An operation returns a streaming response versus a JSON response.
- Adapter processing raises an exception or returns a result that cannot be
  serialized.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Each token lifecycle state and ChatKit errors are visible on the
  chat page without exposing token contents.
- **SC-002**: All four specified protocol operations pass authenticated test
  client checks for successful status, expected response shape, and content
  type.
- **SC-003**: The complete frontend suite, frontend production build, and
  backend suite pass.

## Scope Boundaries

- Preserve the existing chat feature design and same-origin backend route.
- Do not modify todo-item behavior, authentication configuration, dashboard
  behavior, environment values, or production credentials.
- Do not commit, stage, push, or delete files.

## Approved-Scope Amendment

The amendment from `docs/fix.txt` adds these requirements:

- The ChatKit host MUST have a visible wrapper with a concrete height and a
  visible 1px border; the custom element MUST receive full-size block styling.
  Add a frontend regression test for both styles. Only use theme or start-screen
  options supported by the installed `@openai/chatkit-react` types.
- The backend agent adapter MUST await `to_agent_input`, pass the converted
  input to `Runner.run_streamed`, and pass the resulting stream to
  `stream_agent_response`, following the installed `openai-chatkit` API.
  A regression test MUST exercise `threads.create` with warnings treated as
  errors, assert the agent receives converted input, and verify an assistant
  message item in the SSE response.
- MCP tool `user_id` MUST be injected server-side from the verified token and
  MUST NOT be selected by the model.
- Validation MUST include the full backend suite, full frontend suite, and
  frontend production build; report actual test counts and the root cause of
  each fix.
- `Runner.run_streamed` MUST use the installed Agents SDK signature (`input=`)
  and receive ChatKit's `AgentContext` populated with the verified request
  context. MCP tool metadata MUST derive `user_id` from that server-side
  request context. Attached MCP servers MUST be connected for the duration of
  the streamed run and cleaned up afterward. Regression coverage MUST bind the
  call to the installed signature and smoke-test the real Runner with a local
  fake model, without emitting a never-awaited coroutine warning.
