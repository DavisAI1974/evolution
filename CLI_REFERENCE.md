# Evolution CLI Reference

## `status`

Show manifest, observation, requests, and proposals.

```powershell
python evolution.py status
```

## `status-json`

Emit machine-readable status for dashboards.

```powershell
python evolution.py status-json
```

## `observe`

Inspect local project shape.

```powershell
python evolution.py observe
```

## `ask "request"`

Append a human operator request.

```powershell
python evolution.py ask "request"
```

## `requests`

List operator requests.

```powershell
python evolution.py requests
```

## `promote`

Convert open requests into proposals.

```powershell
python evolution.py promote
```

## `discover`

Create proposals from project state signals.

```powershell
python evolution.py discover
```

## `proposals`

List proposal ledger.

```powershell
python evolution.py proposals
```

## `work`

Work the next safe proposal.

```powershell
python evolution.py work
```

## `work --allow-protected`

Permit approved protected-target work.

```powershell
python evolution.py work --allow-protected
```

## `verify`

Run all verification gates.

```powershell
python evolution.py verify
```

## `cycle`

Promote, observe, verify, and write memory.

```powershell
python evolution.py cycle
```
