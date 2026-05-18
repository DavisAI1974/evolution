# Evolution

Evolution is the new home for the self-evolving codebase and AI-first language project.
It starts from the working Nova interpreter seed and wraps it with a guarded evolution
loop: observe, propose, verify, govern, learn.

The project is intentionally one folder. Language runtime, examples, optimizer tools,
docs, memory, and evolution automation all live here.

## Quick Start

```powershell
cd E:\evolution
python nova_interpreter.py homelift_nova_example.nv
python evolution.py status
python evolution.py ask "Add return values to Nova functions"
python evolution.py requests
python evolution.py promote
python evolution.py proposals
python evolution.py work
python evolution.py cycle
python operator_console.py
python -m unittest discover -s tests
```

## What Is Here

- `nova_interpreter.py`: the lightweight Nova language interpreter.
- `nova_token_optimizer.py`: compact data format utilities.
- `nova_mcp_optimizer.py`: consolidated tool execution experiments.
- `evolution.py`: the first self-evolution CLI and guardrail loop.
- `examples/evolution_loop.nv`: Nova script describing the language's own loop.
- `examples/functions.nv`: first self-hosting language feature example.
- `tests/`: regression tests that protect the interpreter before syntax changes.
- `memory/evolution_memory.jsonl`: append-only learning log created by cycles.
- `requests/evolution_requests.jsonl`: append-only human operator requests.
- `proposals/evolution_proposals.jsonl`: promoted request records with risk, target, and gate.
- `operator_console.py`: local prompt loop for human operator input.
- `EVOLUTION_WORKFLOW.md`: step-by-step request to proposal to verification workflow.

## Work Command

Use `python evolution.py work` to let Evolution pick the next actionable proposal.
Protected files such as `nova_interpreter.py` are marked `needs_approval` unless
you deliberately rerun with `--allow-protected`.
- `project.evolution.json`: project identity, gates, and promotion policy.

## Current Evolution Loop

```text
observe -> propose -> verify -> govern -> learn
```

The first implementation is conservative. It does not rewrite code automatically.
It inspects the project, produces proposal records, runs verification commands,
and stores the result in local memory. The next step is to let verified proposals
open patches behind a review gate.

## Why Start From Nova

The DavisAI `nova-lang` folder was mostly a FastAPI placeholder. This project starts
from the fuller Nova seed in `E:\homelift_projects\nova_homelift_complete`, which
already included:

- a runnable interpreter,
- `.nv` examples,
- token compression tools,
- MCP/tool consolidation experiments,
- architecture and integration docs.

## Project Rule

Evolution can suggest changes to itself, but promotion requires evidence. A change
must attach a verification result before it can move from proposal to candidate.

## Language Notes

Nova now supports lightweight user-defined functions:

```nova
fn announce(stage) {
    print("evolving: " + stage)
}

announce("verify")
```
