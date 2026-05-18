#!/usr/bin/env python3
"""
Local human operator console for Evolution.

This intentionally stays tiny: the source of truth is still evolution.py and the
append-only request log.
"""

from __future__ import annotations

from evolution import append_request, read_requests


def main() -> int:
    print("Evolution Operator Console")
    print("Type a request and press Enter. Commands: /list, /quit")
    while True:
        try:
            text = input("evolution> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue
        if text in {"/quit", "/exit"}:
            return 0
        if text == "/list":
            for request in read_requests():
                print(f"{request.get('id', 'REQ-????')} [{request.get('status')}] {request.get('request')}")
            continue
        event = append_request(text)
        print(f"captured {event['id']}")


if __name__ == "__main__":
    raise SystemExit(main())
