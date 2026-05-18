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
        ],
    )
    parser.add_argument("text", nargs="*", help="Request text for the ask command")
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
