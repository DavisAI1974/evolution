# Evolution Invention Disclosure Notes

This document is an engineering disclosure note, not legal advice and not a
patent filing. It exists to capture the technical shape of the invention early
so a patent attorney can evaluate novelty, claims, prior art, and filing timing.

## Working Title

Guarded Self-Evolution System for an AI-First Programming Language and Codebase

## Core Idea

A software project maintains a local, append-only evolution system that can:

1. Capture human operator requests.
2. Promote requests into auditable proposals.
3. Discover new proposals from project state without direct human prompting.
4. Classify proposals by target, risk, and verification gate.
5. Work safe proposals automatically.
6. Block protected runtime/language changes until durable approval exists.
7. Verify changes through executable language examples, tests, and CI gates.
8. Record outcomes in append-only memory.

## Potentially Distinctive Claims To Explore

- A local self-evolution ledger that links requests, proposals, work attempts,
  verification results, and memory events by stable IDs.
- A protected-target governor that allows autonomous work on safe surfaces while
  requiring explicit approval for interpreter/runtime modification.
- A discovery brain that generates new proposals from structural project signals
  such as repeated approval bottlenecks, missing examples, stale state summaries,
  and completed work without changelog entries.
- An AI-first language evolution workflow where executable examples and parser
  tests are required before syntax evolution.
- A self-readable state file generated from append-only memory to preserve
  continuity across agent sessions.

## Current Prototype Artifacts

- `evolution.py`
- `operator_console.py`
- `requests/evolution_requests.jsonl`
- `proposals/evolution_proposals.jsonl`
- `discovery/evolution_discoveries.jsonl`
- `memory/evolution_memory.jsonl`
- `CURRENT_STATE.md`
- `.github/workflows/verify.yml`

## Filing Caution

Public disclosure can affect patent rights. Before public demos, blog posts,
open-source announcements, or broad sharing, talk to a qualified patent attorney.
