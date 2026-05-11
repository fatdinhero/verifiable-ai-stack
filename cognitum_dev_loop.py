"""
COGNITUM — Autonomous Dev Loop (cognitum_dev_loop.py)
Liest Tasks aus dev_queue.yaml, generiert Code via LLM,
führt pytest aus, committet bei Coverage >= 80%.

Konfiguration via .env:
  MIMO_BASE_URL   — LLM API Endpunkt (Standard: Ollama lokal)
  MIMO_API_KEY    — Bearer Token (optional bei Ollama)
  MIMO_MODEL      — Modellname (Standard: qwen2.5:7b)
"""

from __future__ import annotations

import ast as _ast
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

BASE_DIR = Path(__file__).parent
ENV_PATH = BASE_DIR / ".env"
QUEUE_PATH = BASE_DIR / "dev_queue.yaml"

MAX_ITERATIONS = 8
COVERAGE_TARGET = 80


# ── ENV ─────────────────────────────────────────────────────────────────────

def load_env() -> dict:
    env: dict = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

ENV = load_env()

LLM_BASE  = ENV.get("MIMO_BASE_URL", "http://localhost:11434")
LLM_KEY   = ENV.get("MIMO_API_KEY", "")
LLM_MODEL = ENV.get("MIMO_MODEL", "qwen2.5:7b")


# ── LLM CLIENT ──────────────────────────────────────────────────────────────

def llm_generate(prompt: str, max_tokens: int = 4096) -> str:
    """Call LLM via OpenAI-compatible endpoint or Ollama."""
    if "/v1" in LLM_BASE or LLM_KEY:
        base = LLM_BASE.rstrip("/")
        url  = f"{base}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if LLM_KEY:
            headers["Authorization"] = f"Bearer {LLM_KEY}"
        payload = {
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
        }
        r = requests.post(url, headers=headers, json=payload, timeout=180)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"].strip()

    url = f"{LLM_BASE}/api/generate"
    payload = {
        "model": LLM_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    r = requests.post(url, json=payload, timeout=180)
    r.raise_for_status()
    return r.json().get("response", "").strip()


# ── QUEUE I/O ────────────────────────────────────────────────────────────────

def load_queue() -> dict:
    return yaml.safe_load(QUEUE_PATH.read_text()) or {"tasks": []}

def save_queue(q: dict) -> None:
    QUEUE_PATH.write_text(yaml.dump(q, allow_unicode=True, sort_keys=False))

def next_pending(q: dict) -> dict | None:
    return next((t for t in q["tasks"] if t["status"] == "PENDING"), None)


# ── CODE EXTRACTION ──────────────────────────────────────────────────────────

def extract_code(response: str) -> str:
    """Aggressively strip all markdown and extract pure Python code."""
    # Primary: ```python ... ```
    m = re.search(r"```python\s*([\s\S]*?)```", response)
    if m:
        return m.group(1).strip()
    # Secondary: any ``` ... ```
    m = re.search(r"```\s*([\s\S]*?)```", response)
    if m:
        return m.group(1).strip()
    # Tertiary: find first Python keyword line and take everything from there
    lines = response.strip().splitlines()
    start = next(
        (i for i, line in enumerate(lines)
         if re.match(r"\s*(import |from |class |def |#)", line)),
        0
    )
    cleaned = [
        line for line in lines[start:]
        if not re.fullmatch(r"`{1,4}(?:python)?", line.strip())
    ]
    return "\n".join(cleaned).strip()


# ── PYTEST + COVERAGE ────────────────────────────────────────────────────────

def run_tests(target: Path, test_file: Path) -> tuple[bool, float, str]:
    """Run pytest with coverage using module name (not path) for reliable measurement."""
    cov_src = target.parent.name  # e.g. "cognitum_governance"
    result = subprocess.run(
        [
            sys.executable, "-m", "pytest",
            str(test_file),
            f"--cov={cov_src}",
            "--cov-report=term-missing",
            "-v", "--tb=short",
        ],
        capture_output=True, text=True, cwd=BASE_DIR
    )
    output = result.stdout + result.stderr

    coverage = 0.0
    m = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if m:
        coverage = float(m.group(1))

    passed = result.returncode == 0
    return passed, coverage, output


# ── GIT COMMIT ───────────────────────────────────────────────────────────────

def git_commit(target: Path, test_file: Path, module: str) -> None:
    subprocess.run(["git", "add", str(target), str(test_file)], cwd=BASE_DIR, check=True)
    msg = f"feat: {module} — autonomous implementation"
    subprocess.run(["git", "commit", "-m", msg], cwd=BASE_DIR, check=True)
    print(f"  ✅ Committed: {msg}")


# ── PROMPTS ──────────────────────────────────────────────────────────────────

def build_impl_prompt(task: dict) -> str:
    return (
        f"Write only the Python implementation for the following specification.\n"
        f"Output ONLY raw Python code. No markdown fences, no backticks, no explanation.\n"
        f"Start directly with 'import' or 'from' or 'class' or 'def'.\n\n"
        f"Module: {task['target']}\n\n"
        f"Specification:\n{task['spec']}\n\n"
        f"Rules:\n"
        f"- Full implementation, no placeholders, no TODOs\n"
        f"- Include type hints and docstrings\n"
        f"- No external dependencies beyond stdlib and SQLite\n"
    )

def build_test_prompt(task: dict, impl_code: str) -> str:
    return (
        f"Write pytest tests for the following Python implementation.\n"
        f"Output ONLY raw Python test code. No markdown fences, no backticks, no explanation.\n"
        f"Start directly with 'import' or 'from'.\n\n"
        f"Module under test: {task['target']}\n\n"
        f"Implementation:\n{impl_code}\n\n"
        f"Rules:\n"
        f"- Use only pytest (no additional test libraries)\n"
        f"- Achieve >= {COVERAGE_TARGET}% coverage\n"
        f"- Import the module correctly: e.g. 'from {task['target'].replace('/', '.').replace('.py', '')} import ...'\n"
        f"- Write at least 5 test functions covering all methods\n"
    )

def build_fix_impl_prompt(task: dict, impl_code: str, test_output: str) -> str:
    return (
        f"Fix the following Python implementation so its tests pass.\n"
        f"Output ONLY raw Python code. No markdown fences, no backticks, no explanation.\n"
        f"Start directly with 'import' or 'from' or 'class' or 'def'.\n\n"
        f"Module: {task['target']}\n\n"
        f"Specification:\n{task['spec']}\n\n"
        f"Current implementation:\n{impl_code}\n\n"
        f"Test errors:\n{test_output[-2000:]}\n"
    )

def build_fix_test_prompt(
    task: dict, impl_code: str, test_code: str,
    test_output: str, coverage: float
) -> str:
    return (
        f"Fix the following pytest tests to achieve >= {COVERAGE_TARGET}% coverage "
        f"(currently {coverage:.0f}%).\n"
        f"Output ONLY raw Python test code. No markdown fences, no backticks, no explanation.\n"
        f"Start directly with 'import' or 'from'.\n\n"
        f"Module: {task['target']}\n\n"
        f"Implementation:\n{impl_code}\n\n"
        f"Current tests:\n{test_code}\n\n"
        f"Test output:\n{test_output[-2000:]}\n"
        f"\nCritical: Use correct import path: "
        f"'from {task['target'].replace('/', '.').replace('.py', '')} import ...'\n"
    )


# ── MAIN LOOP ────────────────────────────────────────────────────────────────

def _derive_test_path(target: Path) -> Path:
    return BASE_DIR / "tests" / f"test_{target.stem}.py"


def process_task(task: dict, q: dict) -> None:
    target    = BASE_DIR / task["target"]
    test_file = _derive_test_path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    test_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"\n{'═'*55}")
    print(f" Module : {task['module']}")
    print(f" Target : {task['target']}")
    print(f" Tests  : {test_file.relative_to(BASE_DIR)}")
    print(f"{'═'*55}")

    init_file = target.parent / "__init__.py"
    if not init_file.exists():
        init_file.write_text("", encoding="utf-8")
        print(f"  Created {init_file}")

    current_impl  = ""
    current_tests = ""

    for iteration in range(1, MAX_ITERATIONS + 1):
        task["iterations"] = iteration
        save_queue(q)

        print(f"\n▶ Iteration {iteration}/{MAX_ITERATIONS}")

        try:
            # ── Call 1: Implementation ────────────────────────────────────
            if iteration == 1:
                print("  Call 1 — Generating implementation…")
                current_impl = extract_code(
                    llm_generate(build_impl_prompt(task))
                )
            else:
                print("  Call 1 — Fixing implementation…")
                current_impl = extract_code(
                    llm_generate(build_fix_impl_prompt(
                        task, current_impl, task.get("last_error", "")
                    ))
                )

            if not current_impl:
                raise RuntimeError("Empty implementation returned by LLM")

            target.write_text(current_impl, encoding="utf-8")
            print(f"  Written impl : {target} ({len(current_impl)} chars)")

            # ── Call 2: Tests ─────────────────────────────────────────────
            if iteration == 1:
                print("  Call 2 — Generating tests…")
                current_tests = extract_code(
                    llm_generate(build_test_prompt(task, current_impl))
                )
            else:
                print("  Call 2 — Fixing tests…")
                current_tests = extract_code(
                    llm_generate(build_fix_test_prompt(
                        task, current_impl, current_tests,
                        task.get("last_error", ""),
                        task.get("coverage") or 0
                    ))
                )

            if not current_tests:
                raise RuntimeError("Empty test file returned by LLM")

            # Validate syntax before writing
            try:
                _ast.parse(current_tests)
            except SyntaxError as se:
                raise RuntimeError(f"Test syntax error: {se}") from se

            test_file.write_text(current_tests, encoding="utf-8")
            print(f"  Written tests: {test_file} ({len(current_tests)} chars)")

        except Exception as e:
            print(f"  ❌ LLM error: {e}")
            task["last_error"] = str(e)
            save_queue(q)
            continue

        # ── Run pytest ────────────────────────────────────────────────────
        print("  Running pytest…")
        passed, coverage, test_output = run_tests(target, test_file)
        task["coverage"] = coverage
        print(f"  Coverage: {coverage:.0f}%  |  Passed: {passed}")

        if coverage >= COVERAGE_TARGET:
            task["status"] = "DONE"
            save_queue(q)
            git_commit(target, test_file, task["module"])
            print(f"\n  ✅ DONE — Coverage {coverage:.0f}% >= {COVERAGE_TARGET}%")
            return

        task["last_error"] = test_output[-1500:]
        save_queue(q)
        print(f"  ⚠️  Coverage {coverage:.0f}% < {COVERAGE_TARGET}% — retrying…")

    task["status"] = "MANUAL_REVIEW"
    save_queue(q)
    print(
        f"\n  🔴 MANUAL_REVIEW — {MAX_ITERATIONS} iterations exhausted, "
        f"coverage {task.get('coverage', 0):.0f}%"
    )


def main() -> None:
    if not QUEUE_PATH.exists():
        print(f"❌ {QUEUE_PATH} not found")
        sys.exit(1)

    print(f"COGNITUM Dev Loop — {datetime.now(timezone.utc).isoformat()}")
    print(f"LLM : {LLM_BASE}  model={LLM_MODEL}\n")

    q = load_queue()

    while task := next_pending(q):
        process_task(task, q)

    done  = sum(1 for t in q["tasks"] if t["status"] == "DONE")
    total = len(q["tasks"])
    print(f"\n{'─'*55}")
    print(f" {done}/{total} modules complete")
    print(f"{'─'*55}")


if __name__ == "__main__":
    main()
