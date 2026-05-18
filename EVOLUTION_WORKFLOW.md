# Evolution Operator Workflow

This is the workflow for moving a human idea into an auditable Evolution change.

## 1. Capture

Use either command line input:

```powershell
python evolution.py ask "Add return values to Nova functions"
```

Or launch the local prompt window:

```powershell
python operator_console.py
```

Requests are stored in:

```text
requests/evolution_requests.jsonl
```

## 2. Promote

Turn open requests into proposal records:

```powershell
python evolution.py promote
python evolution.py proposals
```

Proposals are stored in:

```text
proposals/evolution_proposals.jsonl
```

## 3. Verify

Before any code change is considered safe, run:

```powershell
python evolution.py verify
```

The same gate runs in GitHub Actions on every push and pull request.

## 4. Work

Let Evolution pick the next actionable proposal:

```powershell
python evolution.py work
```

Protected files such as `nova_interpreter.py` require explicit approval:

```powershell
python evolution.py work --allow-protected
```

The first worker version can complete existing safe artifacts, generate
`CURRENT_STATE.md`, and mark protected proposals as `needs_approval`.

## 5. Cycle

Run a full observe, promote, verify, learn cycle:

```powershell
python evolution.py cycle
```

Cycle results are appended to:

```text
memory/evolution_memory.jsonl
```

## 6. Implement

Pick one proposal, make a small scoped change, add tests or examples, run
verification, then commit and push.

Protected targets such as `nova_interpreter.py` need regression tests before
syntax behavior changes.

## 7. Dashboard

The local app or another UI can read machine-friendly status with:

```powershell
python evolution.py status-json
```
