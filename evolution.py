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


def run_cycle() -> dict[str, Any]:
    obs = observe()
    proposals = propose(obs)
    verification = verify()
    event = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "observation": asdict(obs),
        "proposals": [asdict(item) for item in proposals],
        "verification": verification,
        "passed": all(item["ok"] for item in verification),
    }
    append_memory(event)
    return event


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def main() -> int:
    parser = argparse.ArgumentParser(description="Evolution project CLI")
    parser.add_argument("command", choices=["status", "observe", "propose", "verify", "cycle"])
    args = parser.parse_args()

    if args.command == "status":
        manifest = load_manifest()
        print_json({"manifest": manifest, "observation": asdict(observe())})
        return 0
    if args.command == "observe":
        print_json(asdict(observe()))
        return 0
    if args.command == "propose":
        print_json([asdict(item) for item in propose(observe())])
        return 0
    if args.command == "verify":
        results = verify()
        print_json(results)
        return 0 if all(item["ok"] for item in results) else 1
    if args.command == "cycle":
        event = run_cycle()
        print_json(event)
        return 0 if event["passed"] else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
