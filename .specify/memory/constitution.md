<!-- BEGIN SYNC IMPACT REPORT (temporary scratch - remove before commit)
  Sync Impact Report - Constitution Amendment
  Version change: unversioned scaffold -> 1.0.0
  Modified principles: none (initial drafting)
  Added sections: Core Principles (I-V), Additional Constraints, Development Workflow, Governance
  Removed sections: none
  Deferred TODOs: none
END -->

# Todo App Constitution

## Core Principles

### I. Spec-First (NON-NEGOTIABLE)

Every feature MUST begin as a written specification before any implementation work. The
specification MUST describe observable behavior, MUST be approved by the user, and MUST be
implemented from that approved contract.

Rationale: Capturing intent before code prevents rework, keeps scope explicit, and makes every
feature reviewable against an agreed contract.

### II. Test-First (NON-NEGOTIABLE)

Tests MUST be written and user-approved before feature implementation begins. Implementation MUST
follow the red-green-refactor cycle: write a failing test, make it pass, then refactor. A feature is
not complete until all approved tests pass.

Rationale: Tests encode the approved behavior as an executable contract, guarding against silent
regressions as the app evolves.

### III. Feature Lifecycle & Review Gates

Each feature MUST pass the full Spec Kit cycle in order: specify, plan, tasks, implement. Every gate
(spec review, plan review, task review, implementation checklist) MUST be explicitly approved before
the next stage begins. No stage MAY be skipped.

Rationale: Stage-gated delivery keeps changes small, reviewed, and traceable from intent to code.

### IV. Versioning & Breaking Changes

The project and its constitution MUST use semantic versioning (MAJOR.MINOR.PATCH). A change that
breaks existing behavior or governance MUST require a MAJOR bump and an explicit specification
amendment before it is merged. Any breaking change MUST be documented in release notes.

Rationale: Predictable version contracts let contributors and consumers reason about impact before
upgrading.

### V. Simplicity & CLI Usability

The app MUST stay simple, prefer the smallest design that satisfies the approved specification, and
avoid speculative features (YAGNI). Where the app exposes a CLI, it MUST use a clear text-in /
text-out protocol: data on stdout, errors on stderr, and JSON support where interoperability is
needed.

Rationale: Simple text I/O keeps the app debuggable and scriptable; minimal designs are cheaper to
test, maintain, and evolve.

## Additional Constraints

- Runtime MUST target Python 3.13 or newer as declared in `pyproject.toml`.
- Dependencies MUST be managed with `uv`, and the build backend is `uv_build`; a change requires an
  approved specification amendment.
- Application code MUST live under `src/todo_app`; packages and modules MUST be documented at the
  point of definition.

## Development Workflow

- Features MUST follow the sequence `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`,
  `/speckit.implement`, each producing its artifact under `.specify/features/<feature>/`.
- Specs, plans, and task lists MUST be reviewed and approved before downstream work starts.
- Repository changes MUST be committed with concise, descriptive messages. The constitution file
  MUST only be modified through the constitution amendment process (see Governance).
- Completion of a feature MUST be verified against its task checklist before merge.

## Governance

The constitution supersedes all informal practices and applies to every change in this repository.
Amendments MUST update `.specify/memory/constitution.md`, MUST document the change, and MUST bump
the version per the policy in Principle IV:

- MAJOR: backward-incompatible principle removal or redefinition.
- MINOR: new principle or materially expanded guidance.
- PATCH: clarification, wording, or typo-only refinements.

Each amendment MUST be recorded with today's date as `Last Amended` and reviewed before merge.

The constitution MUST be reviewed during the spec and plan gates of every feature change. Disputes
about interpretation MUST be escalated to the maintainer, resolved, and reflected as an amendment
(usually a PATCH).

**Version**: 1.0.0 | **Ratified**: 2026-09-16 | **Last Amended**: 2026-09-16