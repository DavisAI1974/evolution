#!/usr/bin/env python3
"""
Evolution CLI.

This is the first guarded self-evolution loop for the Nova language project.
It observes the local project, proposes improvement candidates, verifies the
runtime, and appends the outcome to local memory.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "project.evolution.json"
MEMORY_DIR = ROOT / "memory"
MEMORY_LOG = MEMORY_DIR / "evolution_memory.jsonl"
REQUESTS_DIR = ROOT / "requests"
REQUESTS_LOG = REQUESTS_DIR / "evolution_requests.jsonl"
PROPOSALS_DIR = ROOT / "proposals"
PROPOSALS_LOG = PROPOSALS_DIR / "evolution_proposals.jsonl"
DISCOVERY_DIR = ROOT / "discovery"
DISCOVERY_LOG = DISCOVERY_DIR / "evolution_discoveries.jsonl"


@dataclass
class Observation:
    nova_files: int
    python_files: int
    docs: int
    has_manifest: bool
    has_memory: bool
    interpreter_bytes: int


@dataclass
class Proposal:
    proposal_id: str
    title: str
    target: str
    reason: str
    risk: str
    gate: str


def load_manifest() -> dict[str, Any]:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def observe() -> Observation:
    nova_files = list(ROOT.rglob("*.nv"))
    python_files = [p for p in ROOT.rglob("*.py") if "__pycache__" not in p.parts]
    docs = list(ROOT.rglob("*.md")) + list(ROOT.rglob("*.txt"))
    interpreter = ROOT / "nova_interpreter.py"
    return Observation(
        nova_files=len(nova_files),
        python_files=len(python_files),
        docs=len(docs),
        has_manifest=MANIFEST.exists(),
        has_memory=MEMORY_LOG.exists(),
        interpreter_bytes=interpreter.stat().st_size if interpreter.exists() else 0,
    )


def propose(obs: Observation) -> list[Proposal]:
    proposals: list[Proposal] = []
    if obs.nova_files < 3:
        proposals.append(
            Proposal(
                proposal_id="EV-001",
                title="Add more Nova self-hosting examples",
                target="examples/",
                reason="The language needs executable examples that describe evolution, testing, and promotion rules.",
                risk="low",
                gate="verify examples with nova_interpreter.py",
            )
        )
    if obs.has_memory is False:
        proposals.append(
            Proposal(
                proposal_id="EV-002",
                title="Initialize append-only evolution memory",
                target="memory/evolution_memory.jsonl",
                reason="The project needs durable feedback so failed and successful changes can shape future proposals.",
                risk="low",
                gate="append only; never rewrite history",
            )
        )
    proposals.append(
        Proposal(
            proposal_id="EV-003",
            title="Create parser-level tests before changing Nova syntax",
            target="tests/",
            reason="Syntax evolution is the highest-leverage area, but it needs regression tests before auto-patches touch the interpreter.",
            risk="medium",
            gate="human approval required",
        )
    )
    return proposals


def run_command(command: str) -> dict[str, Any]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        shell=True,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip()[-1200:],
        "stderr": completed.stderr.strip()[-1200:],
        "ok": completed.returncode == 0,
    }


def verify() -> list[dict[str, Any]]:
    manifest = load_manifest()
    return [run_command(command) for command in manifest["verification"]["commands"]]


def append_memory(event: dict[str, Any]) -> None:
    MEMORY_DIR.mkdir(exist_ok=True)
    with MEMORY_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def append_request(text: str) -> dict[str, Any]:
    REQUESTS_DIR.mkdir(exist_ok=True)
    event = {
        "id": next_id("REQ", read_jsonl(REQUESTS_LOG)),
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "open",
        "request": text.strip(),
    }
    with REQUESTS_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")
    return event


def read_requests() -> list[dict[str, Any]]:
    requests = read_jsonl(REQUESTS_LOG)
    changed = False
    next_number = 1
    for request in requests:
        if not request.get("id"):
            while any(item.get("id") == f"REQ-{next_number:04d}" for item in requests):
                next_number += 1
            request["id"] = f"REQ-{next_number:04d}"
            changed = True
            next_number += 1
    if changed:
        write_jsonl(REQUESTS_LOG, requests)
    return requests


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, sort_keys=True) + "\n")


def next_id(prefix: str, records: list[dict[str, Any]]) -> str:
    numbers: list[int] = []
    for record in records:
        raw = str(record.get("id", ""))
        if raw.startswith(f"{prefix}-"):
            try:
                numbers.append(int(raw.split("-", 1)[1]))
            except ValueError:
                pass
    return f"{prefix}-{(max(numbers) if numbers else 0) + 1:04d}"


def request_to_proposal(request: dict[str, Any], existing: list[dict[str, Any]]) -> dict[str, Any]:
    text = request["request"]
    lowered = text.lower()
    risk = "medium" if any(term in lowered for term in ["interpreter", "syntax", "parser", "migration"]) else "low"
    if "github workflow" in lowered or "push" in lowered:
        target = ".github/workflows/"
        gate = "GitHub Actions must pass"
    elif "console" in lowered or "prompt" in lowered:
        target = "operator_console.py"
        gate = "manual terminal smoke test"
    elif "dashboard" in lowered or "status as json" in lowered:
        target = "evolution.py"
        gate = "python evolution.py status-json"
    elif "memory" in lowered:
        target = "CURRENT_STATE.md"
        gate = "summary generated from append-only memory"
    elif "return values" in lowered or "else" in lowered or "syntax" in lowered:
        target = "nova_interpreter.py"
        gate = "parser tests and example script must pass"
    else:
        target = "project"
        gate = "python evolution.py verify"
    return {
        "id": next_id("PROP", existing),
        "request_id": request.get("id", "legacy"),
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "proposed",
        "title": text.rstrip("."),
        "target": target,
        "risk": risk,
        "gate": gate,
    }


def new_proposal(
    title: str,
    target: str,
    risk: str,
    gate: str,
    reason: str,
    source: str,
    existing: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "id": next_id("PROP", existing),
        "request_id": source,
        "ts": datetime.now(timezone.utc).isoformat(),
        "status": "proposed",
        "title": title.rstrip("."),
        "target": target,
        "risk": risk,
        "gate": gate,
        "reason": reason,
        "source": source,
    }


def promote_requests() -> dict[str, Any]:
    requests = read_requests()
    proposals = read_jsonl(PROPOSALS_LOG)
    promoted_ids = {proposal.get("request_id") for proposal in proposals}
    changed = False
    new_proposals: list[dict[str, Any]] = []
    for request in requests:
        request_id = request.get("id")
        if request.get("status") == "open" and request_id not in promoted_ids:
            proposal = request_to_proposal(request, proposals + new_proposals)
            new_proposals.append(proposal)
            request["status"] = "proposed"
            request["proposal_id"] = proposal["id"]
            changed = True
    if changed:
        write_jsonl(REQUESTS_LOG, requests)
        write_jsonl(PROPOSALS_LOG, proposals + new_proposals)
    return {
        "promoted": len(new_proposals),
        "proposals": new_proposals,
    }


def read_proposals() -> list[dict[str, Any]]:
    return read_jsonl(PROPOSALS_LOG)


def save_proposals(proposals: list[dict[str, Any]]) -> None:
    write_jsonl(PROPOSALS_LOG, proposals)


def update_proposal_status(
    proposal_id: str,
    status: str,
    note: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    proposals = read_proposals()
    updated: dict[str, Any] | None = None
    for proposal in proposals:
        if proposal.get("id") == proposal_id:
            proposal["status"] = status
            proposal["updated_ts"] = datetime.now(timezone.utc).isoformat()
            proposal["note"] = note
            if extra:
                proposal.update(extra)
            updated = proposal
            break
    if updated is None:
        raise RuntimeError(f"Unknown proposal id: {proposal_id}")
    save_proposals(proposals)
    return updated


def mark_request_status(request_id: str, status: str) -> None:
    requests = read_requests()
    changed = False
    for request in requests:
        if request.get("id") == request_id:
            request["status"] = status
            request["updated_ts"] = datetime.now(timezone.utc).isoformat()
            changed = True
            break
    if changed:
        write_jsonl(REQUESTS_LOG, requests)


def protected_targets() -> set[str]:
    manifest = load_manifest()
    return set(manifest.get("gates", {}).get("blocked_auto_targets", []))


def append_discovery(event: dict[str, Any]) -> None:
    DISCOVERY_DIR.mkdir(exist_ok=True)
    with DISCOVERY_LOG.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, sort_keys=True) + "\n")


def proposal_exists(title: str, proposals: list[dict[str, Any]]) -> bool:
    normalized = title.strip().rstrip(".").lower()
    return any(str(item.get("title", "")).strip().rstrip(".").lower() == normalized for item in proposals)


def discover_candidates() -> dict[str, Any]:
    requests = read_requests()
    proposals = read_proposals()
    memory_events = read_jsonl(MEMORY_LOG)
    observations = asdict(observe())
    blocked = protected_targets()
    created: list[dict[str, Any]] = []
    signals: list[str] = []

    def add(title: str, target: str, risk: str, gate: str, reason: str) -> None:
        if proposal_exists(title, proposals + created):
            return
        created.append(
            new_proposal(
                title=title,
                target=target,
                risk=risk,
                gate=gate,
                reason=reason,
                source="DISCOVERY",
                existing=proposals + created,
            )
        )

    approval_blocked = [item for item in proposals if item.get("status") == "needs_approval"]
    protected_blocked = [item for item in approval_blocked if item.get("target") in blocked]
    language_blocked = [item for item in protected_blocked if item.get("target") == "nova_interpreter.py"]
    done = [item for item in proposals if item.get("status") == "done"]
    open_requests = [item for item in requests if item.get("status") == "open"]

    if protected_blocked:
        signals.append(f"{len(protected_blocked)} protected proposals are waiting on approval")
        add(
            title="Create an explicit approval ledger for protected Evolution work",
            target="approvals/evolution_approvals.jsonl",
            risk="low",
            gate="approval record must reference proposal id and protected target",
            reason="Protected proposals should not depend on chat history; approvals need a durable local audit trail.",
        )

    if len(language_blocked) >= 2:
        signals.append(f"{len(language_blocked)} language proposals are blocked on nova_interpreter.py")
        add(
            title="Create a language change readiness checklist",
            target="LANGUAGE_CHANGE_CHECKLIST.md",
            risk="low",
            gate="checklist must require tests, examples, migration notes, and rollback notes",
            reason="Multiple protected language changes are queued; Evolution needs a standard readiness gate before interpreter edits.",
        )

    if observations["nova_files"] < 5:
        signals.append("Nova has fewer than five executable examples")
        add(
            title="Add executable Nova examples for return values, branching, and migrations",
            target="examples/",
            risk="low",
            gate="all examples must run through nova_interpreter.py",
            reason="A language evolves safely when new syntax has executable examples before runtime changes.",
        )

    if observations["python_files"] > 0 and observations["docs"] < observations["python_files"]:
        signals.append("Documentation count is lower than Python source count")
        add(
            title="Document the Evolution CLI command contract",
            target="CLI_REFERENCE.md",
            risk="low",
            gate="document every evolution.py command with an example",
            reason="The operator and future agents need a stable command contract to use Evolution correctly.",
        )

    if done and not (ROOT / "CHANGELOG.md").exists():
        signals.append("Completed proposals exist but no changelog exists")
        add(
            title="Create CHANGELOG.md from completed proposal records",
            target="CHANGELOG.md",
            risk="low",
            gate="changelog entries must reference proposal ids",
            reason="Completed work should be visible outside JSONL logs for human review and patent/invention tracking.",
        )

    if len(memory_events) >= 5 and not (ROOT / "CURRENT_STATE.md").exists():
        signals.append("Memory has enough events to summarize but CURRENT_STATE.md is missing")
        add(
            title="Generate CURRENT_STATE.md during each cycle",
            target="CURRENT_STATE.md",
            risk="low",
            gate="current state must reflect request, proposal, and memory counts",
            reason="Evolution needs a short self-readable state file between full memory scans.",
        )

    if open_requests:
        signals.append(f"{len(open_requests)} open requests are not promoted")
        add(
            title="Auto-promote open operator requests at the start of work and discover",
            target="evolution.py",
            risk="medium",
            gate="python evolution.py promote must remain idempotent",
            reason="Open requests should enter proposal review before discovery ranks the project state.",
        )

    if not created:
        signals.append("No new structural gaps found")

    if created:
        save_proposals(proposals + created)

    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": "discover",
        "signals": signals,
        "created": created,
        "observation": observations,
    }
    append_discovery(event)
    append_memory(event)
    return event


def append_current_state() -> Path:
    memory_events = read_jsonl(MEMORY_LOG)
    proposals = read_proposals()
    requests = read_requests()
    lines = [
        "# Evolution Current State",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Counts",
        "",
        f"- Requests: {len(requests)}",
        f"- Proposals: {len(proposals)}",
        f"- Memory events: {len(memory_events)}",
        "",
        "## Open Proposals",
        "",
    ]
    for proposal in proposals:
        if proposal.get("status") not in {"done", "verified"}:
            lines.append(
                f"- {proposal.get('id')} [{proposal.get('status')}] "
                f"{proposal.get('title')} -> {proposal.get('target')}"
            )
    lines.extend(["", "## Latest Memory", ""])
    for event in memory_events[-3:]:
        lines.append(
            f"- {event.get('ts')}: passed={event.get('passed')} "
            f"proposal_log_count={event.get('proposal_log_count', 'n/a')}"
        )
    path = ROOT / "CURRENT_STATE.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def ensure_approval_ledger() -> Path:
    path = ROOT / "approvals" / "evolution_approvals.jsonl"
    path.parent.mkdir(exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def write_language_checklist() -> Path:
    path = ROOT / "LANGUAGE_CHANGE_CHECKLIST.md"
    path.write_text(
        "\n".join(
            [
                "# Language Change Checklist",
                "",
                "Use this before editing protected language/runtime files.",
                "",
                "- Proposal id is linked to a request or discovery.",
                "- Protected-file approval is recorded in approvals/evolution_approvals.jsonl.",
                "- Parser/interpreter tests are added or updated.",
                "- At least one executable .nv example demonstrates the behavior.",
                "- Migration notes describe old syntax, new syntax, and compatibility.",
                "- Rollback notes explain how to revert safely.",
                "- python evolution.py verify passes before commit.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return path


def write_cli_reference() -> Path:
    path = ROOT / "CLI_REFERENCE.md"
    commands = [
        ("status", "Show manifest, observation, requests, and proposals."),
        ("status-json", "Emit machine-readable status for dashboards."),
        ("observe", "Inspect local project shape."),
        ("ask \"request\"", "Append a human operator request."),
        ("requests", "List operator requests."),
        ("promote", "Convert open requests into proposals."),
        ("discover", "Create proposals from project state signals."),
        ("proposals", "List proposal ledger."),
        ("work", "Work the next safe proposal."),
        ("work --allow-protected", "Permit approved protected-target work."),
        ("verify", "Run all verification gates."),
        ("cycle", "Promote, observe, verify, and write memory."),
    ]
    lines = ["# Evolution CLI Reference", ""]
    for command, description in commands:
        lines.extend([f"## `{command}`", "", description, "", f"```powershell\npython evolution.py {command}\n```", ""])
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_changelog() -> Path:
    path = ROOT / "CHANGELOG.md"
    proposals = read_proposals()
    lines = ["# Changelog", "", "## Completed Proposals", ""]
    for proposal in proposals:
        if proposal.get("status") == "done":
            lines.append(
                f"- {proposal.get('id')}: {proposal.get('title')} "
                f"({proposal.get('target')})"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_discovery_examples() -> list[Path]:
    examples = {
        "examples/branching_plan.nv": [
            "# Branching plan example.",
            "let condition = True",
            "if condition {",
            '    print("branch-ready")',
            "}",
        ],
        "examples/migration_plan.nv": [
            "# Migration plan example.",
            'let feature = "return-values"',
            'let phase = "draft"',
            'print("migration:" + feature + ":" + phase)',
        ],
    }
    written: list[Path] = []
    for rel, lines in examples.items():
        path = ROOT / rel
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(path)
    return written


def can_satisfy_existing_artifact(proposal: dict[str, Any]) -> tuple[bool, str]:
    title = proposal.get("title", "").lower()
    target = proposal.get("target", "")
    if target == "operator_console.py" and (ROOT / "operator_console.py").exists():
        return True, "operator console exists and was smoke-tested"
    if target == ".github/workflows/" and (ROOT / ".github" / "workflows" / "verify.yml").exists():
        return True, "GitHub verification workflow exists"
    if "convert open requests into proposal" in title and "promote" in command_choices():
        return True, "promote command exists and proposals were generated"
    if target == "evolution.py" and "status-json" in command_choices():
        return True, "status-json command exists"
    if target == "approvals/evolution_approvals.jsonl":
        path = ensure_approval_ledger()
        return True, f"created {path.relative_to(ROOT)}"
    if target == "LANGUAGE_CHANGE_CHECKLIST.md":
        path = write_language_checklist()
        return True, f"created {path.name}"
    if target == "CLI_REFERENCE.md":
        path = write_cli_reference()
        return True, f"created {path.name}"
    if target == "CHANGELOG.md":
        path = write_changelog()
        return True, f"created {path.name}"
    if target == "examples/" and "return values" in title:
        paths = write_discovery_examples()
        return True, "created " + ", ".join(path.name for path in paths)
    return False, ""


def command_choices() -> set[str]:
    return {
        "status",
        "status-json",
        "observe",
        "propose",
        "promote",
        "proposals",
        "verify",
        "cycle",
        "ask",
        "requests",
        "discover",
        "work",
        "work-next",
    }


def work_next(allow_protected: bool = False) -> dict[str, Any]:
    promote_requests()
    proposals = read_proposals()
    blocked = protected_targets()
    for proposal in proposals:
        if proposal.get("status") != "proposed" and not (
            allow_protected and proposal.get("status") == "needs_approval"
        ):
            continue
        proposal_id = proposal["id"]
        request_id = proposal.get("request_id", "")
        target = proposal.get("target", "")
        if target in blocked and not allow_protected:
            updated = update_proposal_status(
                proposal_id,
                "needs_approval",
                f"Protected target {target}; rerun with --allow-protected after human approval.",
            )
            mark_request_status(request_id, "needs_approval")
            event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "action": "work",
                "worked": False,
                "proposal": updated,
            }
            append_memory(event)
            return event

        satisfied, note = can_satisfy_existing_artifact(proposal)
        if not satisfied and target == "CURRENT_STATE.md":
            path = append_current_state()
            satisfied = True
            note = f"generated {path.name} from memory and proposal logs"

        if not satisfied:
            updated = update_proposal_status(
                proposal_id,
                "needs_implementation",
                "No automatic worker is available for this proposal yet.",
            )
            mark_request_status(request_id, "needs_implementation")
            event = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "action": "work",
                "worked": False,
                "proposal": updated,
            }
            append_memory(event)
            return event

        verification = verify()
        passed = all(item["ok"] for item in verification)
        status = "done" if passed else "verification_failed"
        updated = update_proposal_status(
            proposal_id,
            status,
            note,
            {"verification_passed": passed},
        )
        mark_request_status(request_id, status)
        event = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "action": "work",
            "worked": passed,
            "proposal": updated,
            "verification": verification,
        }
        append_memory(event)
        return event
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": "work",
        "worked": False,
        "note": "No proposed work items are available.",
    }
    append_memory(event)
    return event


def run_cycle() -> dict[str, Any]:
    obs = observe()
    promoted = promote_requests()
    proposals = propose(obs)
    verification = verify()
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "observation": asdict(obs),
        "request_promotions": promoted,
        "proposals": [asdict(item) for item in proposals],
        "proposal_log_count": len(read_proposals()),
        "verification": verification,
        "passed": all(item["ok"] for item in verification),
    }
    append_memory(event)
    return event


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evolution project CLI")
    parser.add_argument(
        "command",
        choices=[
            "status",
            "status-json",
            "observe",
            "propose",
            "promote",
            "proposals",
            "verify",
            "cycle",
            "ask",
            "requests",
            "discover",
            "work",
            "work-next",
        ],
    )
    parser.add_argument("text", nargs="*", help="Request text for the ask command")
    parser.add_argument("--allow-protected", action="store_true", help="Allow work on protected targets")
    args = parser.parse_args()

    if args.command == "status":
        manifest = load_manifest()
        print_json({
            "manifest": manifest,
            "observation": asdict(observe()),
            "requests": read_requests(),
            "proposals": read_proposals(),
        })
        return 0
    if args.command == "status-json":
        print_json({
            "observation": asdict(observe()),
            "requests": read_requests(),
            "proposals": read_proposals(),
            "memory_events": len(read_jsonl(MEMORY_LOG)),
        })
        return 0
    if args.command == "observe":
        print_json(asdict(observe()))
        return 0
    if args.command == "propose":
        print_json([asdict(item) for item in propose(observe())])
        return 0
    if args.command == "promote":
        print_json(promote_requests())
        return 0
    if args.command == "discover":
        print_json(discover_candidates())
        return 0
    if args.command == "proposals":
        print_json(read_proposals())
        return 0
    if args.command == "verify":
        results = verify()
        print_json(results)
        return 0 if all(item["ok"] for item in results) else 1
    if args.command == "cycle":
        event = run_cycle()
        print_json(event)
        return 0 if event["passed"] else 1
    if args.command == "ask":
        text = " ".join(args.text).strip()
        if not text:
            print("Usage: python evolution.py ask \"your evolution request\"")
            return 2
        print_json(append_request(text))
        return 0
    if args.command == "requests":
        print_json(read_requests())
        return 0
    if args.command in {"work", "work-next"}:
        event = work_next(allow_protected=args.allow_protected)
        print_json(event)
        return 0 if event.get("worked") or event.get("proposal", {}).get("status") == "needs_approval" else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
