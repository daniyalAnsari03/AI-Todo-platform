# AGENTS.md

Project-wide source of truth for coding-agent behavior in this repository. Applies to every change, superseding all informal practices. Governed by `.specify/memory/constitution.md` (v1.0.0).

## Stack & Layout (Mandatory)

- Python **3.13+** as declared in `pyproject.toml` and `.python-version`.
- Dependencies managed with **uv**; build backend is **uv_build**.
- Application code **MUST** live under `src/todo_app`; packages/modules documented at point of definition.
- Changing the runtime, dependency manager, build backend, or package layout requires an approved specification amendment.
- Do not invent technologies, architecture, features, or requirements beyond what an approved spec establishes.

## Spec-Kit Lifecycle (Mandatory)

Every feature MUST pass the full cycle **in order**, with no stage skipped:

1. **Specify** — `/speckit.specify`
2. **Plan** — `/speckit.plan`
3. **Tasks** — `/speckit.tasks`
4. **Implement** — `/speckit.implement`

Artifacts are produced under `.specify/features/<feature>/`.

### Approval Gates

Each stage requires explicit user approval before the next starts:

- Spec review approved before planning.
- Plan review approved before task generation.
- Task review approved before implementation.
- Implementation checklist verified against the tasks before merge.

Rejected gates abort the stage; no downstream work starts until approved. Never skip, batch, or self-approve a gate.

## Test-First Development (Mandatory)

- Tests MUST be written and user-approved before feature implementation.
- Follow the **red-green-refactor** cycle: write a failing test, make it pass, then refactor.
- A feature is not complete until all approved tests pass.
- Complete a feature only when its task checklist is fully checked.

## Coding Agents

- **OpenCode** is the implementation coding agent.
- Agents act one stage at a time. Do not implement or modify source code until the previous gates are approved and the Implement stage is reached.
- Commit with concise, descriptive messages. The constitution is amended only via the documented amendment process in its Governance section.

## Verification

- Run the project's tests and `uv`-based checks before reporting a stage complete.
- On completion of a stage, summarize what was done and explicitly state readiness for the next gate.

## Working Mode (user preference)
- Do not ask the user for confirmation, approval or clarification during a task. Make the most reasonable decision, record it in the final report, and keep working until done and verified.
- Ask or stop ONLY before: deleting files, touching the real database/backend auth/env, committing/staging/pushing, or deploying.
- Never ask for screenshots (CLI only).