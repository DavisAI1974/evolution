# Language Change Checklist

Use this before editing protected language/runtime files.

- Proposal id is linked to a request or discovery.
- Protected-file approval is recorded in approvals/evolution_approvals.jsonl.
- Parser/interpreter tests are added or updated.
- At least one executable .nv example demonstrates the behavior.
- Migration notes describe old syntax, new syntax, and compatibility.
- Rollback notes explain how to revert safely.
- python evolution.py verify passes before commit.
