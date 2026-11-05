# Tasks: Console Todo

**Input**: Design documents from `.specify/features/001-console-todo/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are MANDATORY for this feature (constitution Principle II). All tests must be written and user-approved before implementation begins.

**Organization**: Tasks are grouped by implementation phase to support the test-first (red-green-refactor) workflow.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Test Writing (Test-First Gate — MANDATORY)

**Purpose**: Write all tests before any implementation. Tests encode the approved behavior as an executable contract.

**⚠️ CRITICAL**: No implementation work may begin until ALL tests in this phase are written and user-approved.

- [ ] T001 [P] [US1-US4] Write unit tests in `tests/test_store.py` covering:
  - add assigns distinct, sequentially increasing positive IDs
  - add rejects empty/whitespace-only descriptions (no item created)
  - list returns current items with statuses (incl. empty case)
  - complete flips an item's status for a valid existing id
  - complete/already complete behavior
  - complete/non-existent id behavior
  - delete removes an existing item
  - delete/non-existent id behavior
  - invalid (non-numeric, zero, negative) ids rejected
- [ ] T002 [P] [US1-US5, FR-008] Write CLI behavior tests in `tests/test_cli.py` covering:
  - one command per line on stdin, data/confirmations on stdout, errors on stderr
  - list output includes id, description, completion status
  - unknown command prints help
  - `exit` terminates with exit code 0

**Checkpoint**: All tests written and FAIL (RED phase). User reviews and approves tests before proceeding.

---

## Phase 2: Store Implementation (US1-US4)

**Purpose**: Implement the in-memory TodoStore to satisfy test_store.py.

- [ ] T003 [US1-US4] Create `src/todo_app/store.py` with TodoStore class implementing:
  - `add(description)` — creates item with next sequential positive ID; rejects empty descriptions
  - `list_items()` — returns current items with statuses
  - `complete(item_id)` — marks item complete; handles already-complete and non-existent ids
  - `delete(item_id)` — removes item; handles non-existent ids
  - ID validation (non-numeric, zero, negative rejected)

**Checkpoint**: `uv run python -m unittest tests.test_store -v` passes.

---

## Phase 3: CLI Implementation (US1-US5, FR-008)

**Purpose**: Implement the REPL loop and command dispatch to satisfy test_cli.py.

- [ ] T004 [US1-US5, FR-008] Implement REPL loop and command dispatch in `src/todo_app/__init__.py`:
  - Read one command per line from stdin
  - Dispatch: add, list, complete, delete, exit, help
  - Data/confirmations on stdout; errors on stderr
  - `exit` terminates with exit code 0
  - Unknown command prints help message

**Checkpoint**: `uv run python -m unittest tests.test_cli -v` passes.

---

## Phase 4: Integration & Validation

**Purpose**: Verify end-to-end behavior matches all success criteria.

- [ ] T005 Run full test suite: `uv run python -m unittest discover -s tests -v`
- [ ] T006 Run quickstart.md manual validation scenarios and verify all pass

**Checkpoint**: All tests pass; all quickstart scenarios verified. Feature complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Tests)**: No dependencies — starts immediately. BLOCKS all implementation.
- **Phase 2 (Store)**: Depends on Phase 1 completion (tests must be approved).
- **Phase 3 (CLI)**: Depends on Phase 1 completion. Can run in parallel with Phase 2 (different files).
- **Phase 4 (Validation)**: Depends on Phase 2 and Phase 3 completion.

### Within Each Phase

- Phase 1: T001 and T002 can run in parallel (different files).
- Phase 2: Single task (T003).
- Phase 3: Single task (T004).
- Phase 4: T005 before T006.

### Test-First Enforcement

Per constitution Principle II:
1. T001 and T002 must be completed and user-approved before T003 or T004 begin.
2. Tests must FAIL before implementation (red-green-refactor cycle).
3. A task is complete only when its tests pass.

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Verify tests fail before implementing
- Commit after each task or logical group
- Stop at any checkpoint to validate independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
