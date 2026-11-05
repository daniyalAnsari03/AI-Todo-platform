# Phase III close-out report

**Status**: implemented and manually verified 2026-10-25.

The original Hackathon PDF is not present in the repository. Requirement names
below refer to the approved Phase III spec, which restates the PDF requirements.
Manual verification items are based on the user's reported real-browser test
with real OpenAI and Neon.

| Phase III requirement | Status and evidence |
|---|---|
| Natural-language add, list, complete, and delete tasks | Verified manually through `/chat`; MCP unit coverage also passes in `tests/test_mcp_tools.py`. |
| Natural-language task update | Passed automated coverage: `TestMCPTools.test_update_task_success_not_found_isolation_null_safe` in `tests/test_mcp_tools.py`; not separately reported as manually verified. |
| Friendly response for a nonexistent task | Verified manually; related ownership/not-found coverage passes in `tests/test_mcp_tools.py`. |
| Authenticated user isolation | Verified manually; `TestChatApi.test_path_mismatch_403_before_db_access` and `TestChatService.test_another_users_conversation_id_rejected` pass. |
| Conversation persistence and restart resume | Verified manually; `TestChatService.test_restart_resume_build_fresh_service_instance_same_db` passes. |
| PDF endpoint `POST /api/{user_id}/chat` remains available and returns `tool_calls` | Passed: `TestChatApi.test_valid_request_returns_conversation_id_response_tool_calls` in `tests/test_chat_api.py`. |
| ChatKit protocol adapter and `/chat` interface | Adapter tests pass in `tests/test_chatkit_adapter.py`; frontend chat page/panel tests pass, and production build succeeds. |
| Chat table migration | Passed: `TestChatMigration.test_create_chat_tables` in `tests/test_migration.py`. The migration was not run against the real database during this close-out. |
| Production-hosted ChatKit domain allowlisting | Unverified; requires production deployment configuration and `NEXT_PUBLIC_OPENAI_DOMAIN_KEY`. |

## Verification

- Backend: `uv run python -m unittest discover tests` — **194 tests passed**.
- Frontend: `npm test` — **61 tests passed** across 14 files.
- Frontend production build: `npm run build` — **passed**.

## Remaining issues and operational notes

- The MCP stdio subprocess starts for each request and may add latency.
- Conversation history currently has no enforced window limit, so large threads
  can increase request context and cost.
- The backend test run emitted `ResourceWarning`s; they did not fail the suite.
- Existing nullable `todo_item` title/timestamp columns remain unchanged; task
  tools handle nulls, and schema cleanup is a separate follow-up.
- Production-hosted ChatKit requires the configured domain allowlist/key; this
  is not needed for local development.
