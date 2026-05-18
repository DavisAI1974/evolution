#!/usr/bin/env python3
# Nova Interpreter — multiline-aware, string-safe blocks, with stdlib + http fallback

import re
import sys
import math
import json
import time
import asyncio
import os
from types import SimpleNamespace
from pathlib import Path
from typing import Any, Dict, List

# -------- HTTP (httpx if available, else urllib) --------
try:
    import httpx  # type: ignore

    def http_get(url: str) -> str:
        r = httpx.get(url, timeout=10)
        return r.text

    def http_post(url: str, data = None) -> str:
        r = httpx.post(url, json=data or {}, timeout=10)
        return r.text

except Exception:  # fallback
    import urllib.request
    import urllib.error

    def http_get(url: str) -> str:
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            return f"[HTTP GET ERROR] {e}"

    def http_post(url: str, data = None) -> str:
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(data or {}).encode("utf-8"),
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.read().decode("utf-8", errors="replace")
        except Exception as e:
            return f"[HTTP POST ERROR] {e}"


class NovaInterpreter:
    def __init__(self):
        # Nova-defined functions: name -> (arg_names, block_lines)
        self.funcs: Dict[str, Any] = {}
        # External modules (optional, e.g., homelift later)
        self.modules: Dict[str, Any] = {}
        # User/global variables (NOT the env)
        self.globals: Dict[str, Any] = {}

        # -------- Built-in environment (safe) --------
        self.allowed_env: Dict[str, Any] = {
            # Core
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "min": min,
            "max": max,
            "sum": sum,
            "list": list,
            "dict": dict,
            "json": json,
            "print": print,
            "range": range,
            "time": time.time,
            # Filesystem
            "exists": os.path.exists,
            "mkdir": os.makedirs,
            "listdir": os.listdir,
            "read": self._read,
            "write": self._write,
            "append": self._append,
            # Async
            "sleep": self._sleep,
            # Math
            "math": SimpleNamespace(
                sqrt=math.sqrt,
                floor=math.floor,
                ceil=math.ceil,
                sin=math.sin,
                cos=math.cos,
                tan=math.tan,
                pi=math.pi,
                e=math.e,
                log=math.log,
                exp=math.exp,
            ),
            # HTTP
            "http": SimpleNamespace(get=http_get, post=http_post),
            # Toy vectors
            "embed": self._fake_embed,
            "cosine": self._cosine,
            # Toy pipeline
            "pipeline": self._pipeline,
            # Constants
            "True": True,
            "False": False,
            "None": None,
        }

        # -------- Small stdlib bundle --------
        self.stdlib = {
            "trim": lambda s: str(s).strip(),
            "upper": lambda s: str(s).upper(),
            "lower": lambda s: str(s).lower(),
            "starts_with": lambda s, p: str(s).startswith(str(p)),
            "retry": self._retry,
            "csv_write": self._csv_write,
            "csv_read": self._csv_read,
            "print_table": self._print_table,
        }
        self.allowed_env["stdlib"] = SimpleNamespace(**self.stdlib)

    # ================= Files =================
    def _read(self, path: str) -> str:
        return Path(path).read_text(encoding="utf-8")

    def _write(self, path: str, text: str) -> None:
        Path(path).write_text(text, encoding="utf-8")

    def _append(self, path: str, text: str) -> None:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)

    # ================= Async =================
    async def _sleep_async(self, sec: float):
        await asyncio.sleep(max(0.0, float(sec)))

    def _sleep(self, sec: float):
        asyncio.run(self._sleep_async(sec))

    # ================= Vectors =================
    def _fake_embed(self, text: str) -> List[float]:
        return [(ord(c) % 97) / 97.0 for c in str(text)]

    def _cosine(self, a: List[float], b: List[float]) -> float:
        # Check if vectors have same length
        if len(a) != len(b):
            # Pad shorter vector with zeros
            if len(a) < len(b):
                a = a + [0.0] * (len(b) - len(a))
            else:
                b = b + [0.0] * (len(a) - len(b))
        
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1e-9
        nb = math.sqrt(sum(y * y for y in b)) or 1e-9
        return dot / (na * nb)

    # ================= Pipeline =================
    def _pipeline(self, *steps):
        data = None
        for step in steps:
            if callable(step):
                data = step(data)
        return data

    # ================= Stdlib =================
    def _retry(self, attempts: int, delay_ms: int, fn):
        last = None
        for i in range(max(1, int(attempts))):
            try:
                return fn()
            except Exception as e:
                last = e
                if i == attempts - 1:
                    raise
                time.sleep(max(0, delay_ms) / 1000.0)
        if last:
            raise last

    def _csv_write(self, path: str, rows: List[List[Any]], sep: str = ","):
        with open(path, "w", encoding="utf-8", newline="") as f:
            for r in rows:
                f.write(sep.join(map(str, r)) + "\n")

    def _csv_read(self, path: str, sep: str = ",") -> List[List[str]]:
        out: List[List[str]] = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                out.append(line.rstrip("\n").split(sep))
        return out

    def _print_table(self, rows: List[List[Any]]):
        for r in rows:
            print(" | ".join(map(str, r)))

    # ================= Eval =================
    def eval_expr(self, expr: str, scope: Dict[str, Any]) -> Any:
        expr = expr.strip()
        try:
            env = {**self.allowed_env, **self.modules, **scope}
            return eval(expr, {"__builtins__": {}}, env)
        except Exception as e:
            raise RuntimeError(
                f"[Nova Error] Could not evaluate expression: {expr} -> {e}"
            )

    # ================= Multiline accumulator =================
    def _gather_from(self, head: str, lines: List[str], start_index: int):
        """
        Accumulate consecutive lines until (), [], {} are balanced.
        String-safe: ignores brackets inside quotes.
        Returns (combined_expr, next_line_index).
        """
        expr = head.strip()
        bal = {"()": 0, "[]": 0, "{}": 0}

        def feed(s: str):
            inq = None
            esc = False
            for ch in s:
                if inq:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == inq:
                        inq = None
                else:
                    if ch in ("'", '"'):
                        inq = ch
                    elif ch == "(":
                        bal["()"] += 1
                    elif ch == ")":
                        bal["()"] -= 1
                    elif ch == "[":
                        bal["[]"] += 1
                    elif ch == "]":
                        bal["[]"] -= 1
                    elif ch == "{":
                        bal["{}"] += 1
                    elif ch == "}":
                        bal["{}"] -= 1

        feed(expr)
        i = start_index

        def balanced() -> bool:
            return bal["()"] == 0 and bal["[]"] == 0 and bal["{}"] == 0

        while not balanced() and i < len(lines):
            nxt = lines[i].strip()
            expr += " " + nxt
            feed(nxt)
            i += 1
        return expr, i

    # ================= Block collector =================
    def _collect_block(self, lines: List[str], start: int):
        """
        Collect lines until matching '}' for a block that started after a '{' on the previous line.
        String-safe: braces inside quotes are ignored.
        Returns (block_lines, next_index).
        """
        block: List[str] = []
        depth = 1
        i = start

        def delta_for(line: str) -> int:
            d = 0
            inq = None
            esc = False
            for ch in line:
                if inq:
                    if esc:
                        esc = False
                    elif ch == "\\":
                        esc = True
                    elif ch == inq:
                        inq = None
                else:
                    if ch in ("'", '"'):
                        inq = ch
                    elif ch == "{":
                        d += 1
                    elif ch == "}":
                        d -= 1
            return d

        while i < len(lines):
            line = lines[i]
            depth += delta_for(line)
            if depth == 0:
                return block, i + 1
            block.append(line)
            i += 1
        return block, i

    # ================= Function calls =================
    def _call_func(
        self, name: str, arg_src: str, lines: List[str], i: int, scope: Dict[str, Any]
    ) -> int:
        # arg_src starts from '(' on the current line; gather to balance
        args_expr, j = self._gather_from(arg_src, lines, i + 1)

        # Nova-defined function?
        if name in self.funcs:
            arg_names, body = self.funcs[name]
            # Evaluate args as Python tuple
            inner = (
                args_expr[1:-1]
                if args_expr.startswith("(") and args_expr.endswith(")")
                else args_expr
            )
            tuple_expr = (
                f"({inner},)"
                if "," not in inner and inner.strip()
                else f"({inner})"
            )
            args_vals = list(self.eval_expr(tuple_expr, scope))
            local = dict(zip(arg_names, args_vals))
            self._run_block(body, {**scope, **local})
            return j

        # Env/module function: use exactly captured parentheses
        call_expr = f"{name}{args_expr}"
        self.eval_expr(call_expr, scope)
        return j

    # ================= Block runner =================
    def _run_block(self, lines: List[str], scope: Dict[str, Any]):
        i = 0
        while i < len(lines):
            raw = lines[i]
            line = raw.strip()
            if not line or line.startswith("#"):
                i += 1
                continue

            # let name = <expr>   (multiline supported)
            if line.startswith("let "):
                body = line[4:]
                if "=" not in body:
                    raise RuntimeError(f"[Nova Error] Invalid assignment: {line}")
                name, start = body.split("=", 1)
                name = name.strip()
                expr, j = self._gather_from(start, lines, i + 1)
                scope[name] = self.eval_expr(expr, scope)
                i = j
                continue

            # if <cond> { ... }
            if line.startswith("if "):
                cond_text = line[3:]
                if "{" in cond_text:
                    cond_text = cond_text[: cond_text.index("{")].strip()
                else:
                    cond_text = cond_text.strip()
                block, j = self._collect_block(lines, i + 1)
                if self.eval_expr(cond_text, scope):
                    self._run_block(block, scope)
                i = j
                continue

            # for <var> in <expr> { ... }
            if line.startswith("for "):
                rest = line[4:].strip()
                if " in " not in rest:
                    raise RuntimeError(f"[Nova Error] Invalid for syntax: {line}")
                var, rhs = rest.split(" in ", 1)
                var = var.strip()
                iter_expr_text = rhs
                if "{" in iter_expr_text:
                    iter_expr_text = iter_expr_text[: iter_expr_text.index("{")].strip()
                else:
                    iter_expr_text = iter_expr_text.strip()
                block, j = self._collect_block(lines, i + 1)
                iterable = self.eval_expr(iter_expr_text, scope)
                for val in iterable:
                    scope[var] = val
                    self._run_block(block, scope)
                i = j
                continue

            # Function call (identifier followed by '(') — multiline args supported
            m = re.match(r"^([A-Za-z_]\w*)\s*\(", line)
            if m:
                fname = m.group(1)
                arg_src = line[line.index("(") :]
                i = self._call_func(fname, arg_src, lines, i, scope)
                continue

            # Otherwise: raw expression (also multiline-capable)
            expr, j = self._gather_from(line, lines, i + 1)
            self.eval_expr(expr, scope)
            i = j

    # ================= File runner =================
    def run_file(self, filename: str):
        text = Path(filename).read_text(encoding="utf-8")
        lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
        # Execute with *user* scope (self.globals), not the env itself
        self._run_block(lines, self.globals)


# ================= CLI =================
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: nova_interpreter.py <file.nv>")
        sys.exit(1)
    NovaInterpreter().run_file(sys.argv[1])
