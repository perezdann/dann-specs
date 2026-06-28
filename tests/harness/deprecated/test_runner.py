#!/usr/bin/env python3
"""
dann-specs Robust Test Suite Runner

Generates and scores tests against the dann-specs principles and rubric.

Important:
- When --real-llm is used, simulated ("good_response") answers are NEVER used.
- If real LLM cannot be called, the test is marked as failed (score=1.0).
- Use this to honestly evaluate how well different models follow the specification.

New in v2:
- --judge-provider: use an external LLM (e.g. deepseek-v4-pro) as impartial judge
- --repetitions N: run each test N times to measure consistency (mean +/- std)
- --no-judge: fall back to heuristic keyword scoring
- suite "concrete": generates coding tasks with executable verification

llama.cpp / reasoning-model notes:
- Many Qwen3 + llama.cpp setups (used successfully from OpenWebUI with Provider=llama.cpp
  and from Kilo Code / Continue "OpenAI Compatible") extract thinking to `reasoning_content`.
- The harness now falls back to reasoning_content so raw_response contains what the model
  actually emitted. See local/README.md for server flags and curl examples.

Supports:
- Core principles
- Rubric dimensions
- Roles
- Variants
- Concrete (executable verification)
- Workflow

Run with: python tests/harness/test_runner.py --suite all --count 30
"""

import json
import random
import argparse
import time
import statistics
import subprocess
import tempfile
import re
import sys
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Optional, Tuple
import os
from datetime import datetime
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from . import config as llm_config
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    import config as llm_config

if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

CORE_PRINCIPLES = [
    "Think & Frame Before Acting",
    "Simplicity & Minimum Viable",
    "Surgical & Precise Changes",
    "Goal-Driven with Verification",
    "Surface Tradeoffs & Log Decisions",
    "Verification-First Workflow",
    "Agentic Workflow Discipline",
]

RUBRIC_DIMENSIONS = [
    "Framing & Assumptions",
    "Scope Discipline",
    "Simplicity",
    "Verification",
    "Tradeoffs",
]

ROLES = [
    "physician", "lawyer", "accountant", "nurse", "mechanic",
    "electronics-technician", "seamstress", "graphic-designer", "architect",
    "domain-specialist", "researcher", "educator", "reviewer"
]

VARIANTS = [
    "software-development", "research-knowledge", "education-courses",
    "infra-devops", "product-management", "data-analysis", "professional-services"
]


@dataclass
class TestCase:
    id: str
    category: str
    sub_category: str
    prompt: str
    expected_behaviors: List[str]
    good_response: str
    bad_response: str
    rubric_target: Dict[str, int]
    concrete_assertions: List[Dict] = field(default_factory=list)
    forbidden_patterns: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    test_id: str
    category: str
    score: float
    passed: bool
    details: str
    time_seconds: float = 0.0
    prompt_system: str = ""
    prompt_user: str = ""
    raw_response: str = ""
    self_evaluation: Dict = None
    judge_scores: Dict = None
    judge_justification: str = ""
    n_repetitions: int = 1
    std_dev: float = 0.0
    repetition_scores: List[float] = None


class JudgeEvaluator:
    """Uses an external LLM to score test responses against the dann-specs rubric."""

    RUBRIC_PROMPT = """You are an impartial evaluator scoring an AI agent's response against the dann-specs framework.

Evaluate the response on these 5 dimensions (1-5 each):

1. Framing & Assumptions (1-5): Did the agent explicitly state assumptions and unknowns?
2. Scope Discipline (1-5): Were all changes directly traceable to the request (surgical)?
3. Simplicity (1-5): Was the solution the minimal correct one?
4. Verification (1-5): Did the agent provide concrete evidence that success criteria were met?
5. Tradeoffs (1-5): Did the agent surface important decisions and their implications?

Scoring guide:
- 1: Completely absent or violates the principle
- 2: Mentions it vaguely but no substance
- 3: Adequate, some attempt made
- 4: Good, clear evidence of the principle
- 5: Excellent, exemplary application of the principle

The original task was: {task}

The agent's response:
---
{response}
---

Return ONLY a JSON object (no markdown, no backticks):
{{"Framing & Assumptions": N, "Scope Discipline": N, "Simplicity": N, "Verification": N, "Tradeoffs": N, "overall": N.N, "justification": "Brief explanation of key scores (max 200 chars)"}}

overall is the average of the 5 scores rounded to 1 decimal."""

    def __init__(self, client, model: str):
        self.client = client
        self.model = model

    def evaluate(self, test_case: TestCase, response: str) -> Dict:
        resp = (response or "").strip()
        if not resp or resp.startswith("LLM_ERROR") or resp.startswith("ERROR"):
            return {
                "score": 1.0, "passed": False, "details": "empty or error response from LLM",
                "judge_scores": {}, "judge_justification": "no response to evaluate"
            }
        if len(resp) > 10 and resp.count("/") > len(resp) * 0.6:
            return {
                "score": 1.0, "passed": False, "details": "garbage output from provider (slashes)",
                "judge_scores": {}, "judge_justification": "garbage slashes"
            }

        judge_prompt = self.RUBRIC_PROMPT.format(
            task=test_case.prompt[:1500],
            response=resp[:4000]
        )

        try:
            r = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": judge_prompt}],
                temperature=0.0,
                max_tokens=600
            )
            raw_judge = (getattr(r.choices[0].message, "content", None) or "").strip()
            if not raw_judge:
                raw_judge = (getattr(r.choices[0].message, "reasoning_content", None) or "").strip()

            parsed = self._parse_judge_json(raw_judge)
            if parsed:
                scores = {k: float(v) for k, v in parsed.items()
                          if k in RUBRIC_DIMENSIONS and isinstance(v, (int, float))}
                vals = list(scores.values())
                if len(vals) >= 4:
                    avg = round(sum(vals) / len(vals), 1)
                else:
                    avg = float(parsed.get("overall", 2.0))
                return {
                    "score": avg,
                    "passed": avg >= 4.0,
                    "details": f"Judge: avg={avg:.1f}",
                    "judge_scores": scores,
                    "judge_justification": parsed.get("justification", str(raw_judge)[:200])
                }

            return {
                "score": 2.0, "passed": False,
                "details": f"Judge parse failed: {raw_judge[:120]}",
                "judge_scores": {}, "judge_justification": raw_judge[:200]
            }

        except Exception as e:
            return {
                "score": 1.0, "passed": False,
                "details": f"Judge API error: {str(e)[:100]}",
                "judge_scores": {}, "judge_justification": str(e)[:200]
            }

    def _parse_judge_json(self, raw: str) -> Optional[Dict]:
        for candidate in [raw]:
            try:
                return json.loads(candidate)
            except json.JSONDecodeError:
                pass
        m = re.search(r'\{[\s\S]*\}', raw)
        if m:
            try:
                return json.loads(m.group(0))
            except json.JSONDecodeError:
                pass
        return None


class DannSpecsTestHarness:
    def __init__(self, project_root: Path,
                 config_path: Optional[Path] = None,
                 provider: Optional[str] = None,
                 use_real_llm: bool = False,
                 judge_provider: Optional[str] = None,
                 judge_model: Optional[str] = None,
                 repetitions: int = 1):

        self.project_root = project_root
        self.results: List[TestResult] = []
        self.use_real_llm = use_real_llm
        self.llm_client = None
        self.current_provider_name = provider or "env"
        self.current_provider = {}
        self.judge_provider_name = judge_provider
        self.judge_evaluator = None
        self.repetitions = max(1, repetitions)

        cfg = llm_config.load_llm_config(config_path)
        self.llm_config = cfg

        if use_real_llm and OpenAI is not None:
            prov = llm_config.get_provider(cfg, provider)
            self.current_provider = prov
            self.current_provider_name = provider or cfg.get("default_provider", "env")

            base = prov.get("base_url", "http://localhost:8080/v1")
            key = prov.get("api_key", "")
            model = prov.get("model", "local")

            self.llm_client = OpenAI(base_url=base, api_key=key)
            self.model = model

            try:
                models = self.llm_client.models.list()
                ids = [m.id for m in getattr(models, "data", [])]
                if ids:
                    if model.lower() in ("llama", "local", "default", "") or model not in ids:
                        self.model = ids[0]
                        print(f"[INFO] Auto-selected real model from server: {self.model}")
                    else:
                        print(f"[INFO] Using configured model: {self.model}")
                    print(f"[INFO] Available models: {ids[:3]}")
            except Exception:
                pass

            print(f"[INFO] Using provider '{self.current_provider_name}' -> {base} (model={self.model})")

        if judge_provider and OpenAI is not None:
            jprov = llm_config.get_provider(cfg, judge_provider)
            jbase = jprov.get("base_url", "")
            jkey = jprov.get("api_key", "")
            jmodel = judge_model or jprov.get("model", "gpt-4o-mini")
            if jkey and jkey != "DEEPSEEK_API_KEY_PLACEHOLDER":
                self.judge_client = OpenAI(base_url=jbase, api_key=jkey)
                self.judge_evaluator = JudgeEvaluator(self.judge_client, jmodel)
                self.judge_model = jmodel
                print(f"[INFO] Judge evaluator: '{judge_provider}' -> {jbase} (model={jmodel})")
            else:
                print(f"[WARN] Judge provider '{judge_provider}' has no valid API key. Falling back to heuristic scoring.")

    def _call_llm(self, system_prompt: str, user_prompt: str, max_tokens: int = 800) -> str:
        if not self.llm_client:
            return "ERROR: LLM client not initialized"

        def _do_chat(msgs, mt, temp):
            r = self.llm_client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=temp,
                max_tokens=mt
            )
            msg = r.choices[0].message
            content = (getattr(msg, "content", None) or "").strip()
            reasoning = (getattr(msg, "reasoning_content", None) or "").strip()
            if not content and reasoning:
                content = reasoning
            if not content:
                extra = getattr(msg, "model_extra", None) or {}
                content = (extra.get("reasoning_content") or "").strip() or content
            return content or ""

        def _do_completion(prompt, mt, temp):
            r = self.llm_client.completions.create(
                model=self.model,
                prompt=prompt,
                temperature=temp,
                max_tokens=mt
            )
            txt = ""
            if r.choices:
                c0 = r.choices[0]
                txt = getattr(c0, "text", None) or (c0.get("text") if isinstance(c0, dict) else "")
            return (txt or "").strip()

        full_prompt = (system_prompt or "") + "\n\n" + (user_prompt or "")

        try:
            msgs = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            content = _do_chat(msgs, max_tokens, 0.2)
            if content:
                return content
            content = _do_chat(msgs, 400, 0.5)
            if content:
                return content
            content = _do_chat([{"role": "user", "content": full_prompt[:1800]}], 500, 0.3)
            if content:
                return content
            content = _do_completion(full_prompt[:1800], 500, 0.3)
            if content:
                return content
            return ""
        except Exception as e:
            try:
                content = _do_completion(full_prompt[:1500], 400, 0.4)
                if content:
                    return content
            except Exception as e2:
                return f"LLM_ERROR: {str(e)} | legacy_err={str(e2)[:80]}"
            return f"LLM_ERROR: {str(e)}"

    def generate_report(self, suite: str, results: List[TestResult]) -> Path:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        provider = self.current_provider_name.replace("/", "-")
        report_dir = self.project_root / "reports"
        report_dir.mkdir(exist_ok=True)

        n = len(results)
        avg = sum(r.score for r in results) / n if n else 0
        passed = sum(1 for r in results if r.passed)
        total_time = sum(r.time_seconds for r in results)

        report_data = {
            "timestamp": timestamp,
            "provider": provider,
            "suite": suite,
            "total_tests": n,
            "passed": passed,
            "average_score": avg,
            "repetitions": self.repetitions,
            "judge_provider": self.judge_provider_name,
            "judge_model": getattr(self, "judge_model", None),
            "results": [asdict(r) for r in results],
            "config_used": {
                "provider": provider,
                "base_url": self.current_provider.get("base_url", "N/A"),
                "model": getattr(self, "model", self.current_provider.get("model", "N/A"))
            }
        }

        json_path = report_dir / f"{timestamp}-{provider}-{suite}.json"
        with open(json_path, "w") as f:
            json.dump(report_data, f, indent=2)

        avg_time = total_time / n if n else 0
        md_path = report_dir / f"{timestamp}-{provider}-{suite}.md"
        with open(md_path, "w") as f:
            f.write(f"# Test Report - {suite}\n\n")
            f.write(f"**Provider**: {provider} ({report_data['config_used']['model']})\n")
            judge_info = f" | Judge: {self.judge_provider_name}/{getattr(self, 'judge_model', 'none')}" if self.judge_evaluator else ""
            f.write(f"**Date**: {timestamp}{judge_info}\n")
            f.write(f"**Tests**: {n} | **Passed**: {passed} | **Avg Score**: {avg:.2f}\n")
            if self.repetitions > 1:
                avg_std = sum(r.std_dev for r in results) / n if n else 0
                f.write(f"**Repetitions**: {self.repetitions} | **Avg Std Dev**: {avg_std:.2f}\n")
            f.write(f"**Total time**: {total_time:.1f}s | **Avg time per test**: {avg_time:.1f}s\n\n")
            f.write("## Summary\n\n")
            for r in results[:15]:
                status = "OK" if r.passed else "FAIL"
                std_info = f" +/-{r.std_dev:.1f}" if r.repetition_scores and len(r.repetition_scores) > 1 else ""
                se = ""
                if getattr(r, 'self_evaluation', None):
                    se_scores = [v for k, v in r.self_evaluation.items() if isinstance(v, (int, float))]
                    if se_scores:
                        se = f" (self: {sum(se_scores)/len(se_scores):.1f})"
                raw_snip = (getattr(r, 'raw_response', '') or '').replace('\n', ' ')[:90]
                raw_part = f" | '{raw_snip}...'" if raw_snip else ""
                f.write(f"- {status} {r.test_id}: {r.score:.1f}{std_info} ({r.time_seconds:.1f}s) - {r.details[:70]}{se}{raw_part}\n")
            f.write("\n**Note**: Full details (prompts, raw responses, self-evaluations, judge scores) in the .json file.\n")

        print(f"[REPORT] Saved: {json_path}")
        return json_path

    def generate_core_principle_tests(self, count: int = 30) -> List[TestCase]:
        tests = []
        principles = CORE_PRINCIPLES
        base_prompts = [
            "Implement a user authentication system with password reset.",
            "Add a new feature to export reports as PDF.",
            "Refactor the database connection handling.",
            "Fix the bug where users can see other users' data.",
            "Create an API endpoint for searching products.",
            "Update the logging system to be more detailed.",
            "Implement rate limiting on the public API.",
            "Add support for multiple languages in the UI.",
            "Optimize the image upload and processing pipeline.",
            "Create a dashboard for monitoring system health.",
        ]

        for i in range(count):
            principle = principles[i % len(principles)]
            base = base_prompts[i % len(base_prompts)]

            prompt = f"Task: {base}\n\nFollow the dann-specs principles, especially around '{principle}'."

            expected = [principle]
            if "Verification" in principle or "Goal" in principle:
                expected.append("Verification-First Workflow")

            good = (
                f"I will start by clarifying assumptions about the requirements for '{base}'. "
                f"My goal is to [specific verifiable outcome]. I will make only the minimal changes needed. "
                f"After implementation, I will run tests and show the results as evidence."
            )

            bad = (
                f"I'll just add the feature. It should work. "
                f"While I'm at it, I'll also refactor a bunch of unrelated code and add some extra features that might be useful later."
            )

            rubric = {
                "Framing & Assumptions": 4,
                "Scope Discipline": 4 if "Surgical" in principle else 3,
                "Simplicity": 4,
                "Verification": 4,
                "Tradeoffs": 3
            }

            tests.append(TestCase(
                id=f"core-{principle.lower().replace(' ', '-')}-{i:03d}",
                category="core_principles",
                sub_category=principle,
                prompt=prompt,
                expected_behaviors=expected,
                good_response=good,
                bad_response=bad,
                rubric_target=rubric
            ))
        return tests

    def generate_rubric_tests(self, count: int = 30) -> List[TestCase]:
        tests = []
        dimensions = RUBRIC_DIMENSIONS

        scenarios = [
            "Add a simple validation to a form field.",
            "Migrate a legacy module to a new framework.",
            "Debug why a scheduled job is failing intermittently.",
            "Design a new caching layer for the application.",
            "Write documentation for an existing complex feature.",
        ]

        for i in range(count):
            dim = dimensions[i % len(dimensions)]
            scenario = scenarios[i % len(scenarios)]

            prompt = f"Task: {scenario}\nFocus especially on the '{dim}' dimension from the rubric."

            good = f"Before starting, I stated my assumptions clearly. I will only change files directly related to the task. The solution is minimal. After changes, I ran the relevant tests and here are the passing results: [evidence]. Tradeoff considered: X vs Y."

            bad = "I made several changes across the codebase to improve things. The feature should now be better overall."

            rubric = {d: 4 for d in dimensions}
            rubric[dim] = 5

            tests.append(TestCase(
                id=f"rubric-{dim.lower().replace(' ', '-')}-{i:03d}",
                category="rubric_dimensions",
                sub_category=dim,
                prompt=prompt,
                expected_behaviors=[dim],
                good_response=good,
                bad_response=bad,
                rubric_target=rubric
            ))
        return tests

    def generate_role_tests(self, count: int = 30) -> List[TestCase]:
        tests = []
        roles = ROLES

        for i in range(count):
            role = roles[i % len(roles)]
            task = f"Help with a task in the domain of {role.replace('-', ' ')}."

            prompt = f"You are in the role of {role}. {task} Apply dann-specs principles."

            good = f"As a {role}, I will frame the problem according to domain best practices. I will make surgical, minimal changes. I will define clear success criteria and verify them with domain-appropriate checks."

            bad = "I'll just do the task in a general way without considering the specific domain needs of a " + role + "."

            tests.append(TestCase(
                id=f"role-{role}-{i:03d}",
                category="roles",
                sub_category=role,
                prompt=prompt,
                expected_behaviors=[f"Role adherence: {role}"],
                good_response=good,
                bad_response=bad,
                rubric_target={"Scope Discipline": 4, "Verification": 4}
            ))
        return tests

    def generate_variant_tests(self, count: int = 30) -> List[TestCase]:
        tests = []
        variants = VARIANTS

        for i in range(count):
            variant = variants[i % len(variants)]
            base_task = "Build a new feature for data processing."

            prompt = f"Using the {variant} variant of dann-specs: {base_task}"

            good = f"Following the {variant} guidelines, I will [domain specific framing]. I will prioritize [variant specific emphasis like verification in research or simplicity in education]."

            bad = "I'll treat this as a generic software task without adapting to the " + variant + " context."

            tests.append(TestCase(
                id=f"variant-{variant}-{i:03d}",
                category="variants",
                sub_category=variant,
                prompt=prompt,
                expected_behaviors=[f"Variant specific: {variant}"],
                good_response=good,
                bad_response=bad,
                rubric_target={"Framing & Assumptions": 4}
            ))
        return tests

    def generate_concrete_tests(self, count: int = 30) -> List[TestCase]:
        """Generate tests with actually executable, verifiable coding tasks.
        The model must produce code that passes specific assertions.
        """
        tasks = [
            {
                "name": "email_validator",
                "prompt": "Write a Python function `is_valid_email(email: str) -> bool` that validates email addresses. "
                          "Return ONLY the function code (no explanations, no extra functions). "
                          "The function should check for: presence of @, non-empty local part, non-empty domain with a dot.",
                "assertions": [
                    {"input": "test@example.com", "expected": True},
                    {"input": "invalid", "expected": False},
                    {"input": "user@domain", "expected": False},
                    {"input": "@domain.com", "expected": False},
                    {"input": "user@.com", "expected": False},
                ],
                "forbidden": ["def (?!is_valid_email\\b)\\w+", "class ", "import "],
                "principle": "Simplicity & Minimum Viable"
            },
            {
                "name": "fibonacci",
                "prompt": "Write a Python function `fibonacci(n: int) -> list` that returns the first n Fibonacci numbers. "
                          "Return ONLY the function code. Use iteration, not recursion.",
                "assertions": [
                    {"input": 5, "expected": [0, 1, 1, 2, 3]},
                    {"input": 1, "expected": [0]},
                    {"input": 0, "expected": []},
                    {"input": 10, "expected": [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]},
                ],
                "forbidden": ["def (?!fibonacci\\b)\\w+", "class "],
                "principle": "Goal-Driven with Verification"
            },
            {
                "name": "word_counter",
                "prompt": "Write a Python function `count_words(text: str) -> dict` that counts word frequencies. "
                          "Return ONLY the function code. Words are case-insensitive, split by whitespace, ignore punctuation.",
                "assertions": [
                    {"input": "hello world hello", "expected": {"hello": 2, "world": 1}},
                    {"input": "Hello, World! Hello.", "expected": {"hello": 2, "world": 1}},
                    {"input": "", "expected": {}},
                    {"input": "one", "expected": {"one": 1}},
                ],
                "forbidden": ["def (?!count_words\\b)\\w+", "class "],
                "principle": "Verification-First Workflow"
            },
            {
                "name": "surgical_fix",
                "prompt": "You have this buggy function:\n"
                          "```python\ndef calculate_average(numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total / len(numbers)\n```\n"
                          "Fix ONLY the bug (empty list causes ZeroDivisionError). "
                          "Return ONLY the corrected function code. Do NOT add type hints, docstrings, or anything else. "
                          "Do NOT rename the function.",
                "assertions": [
                    {"input": [1, 2, 3], "expected": 2.0},
                    {"input": [], "expected": 0.0},
                    {"input": [5], "expected": 5.0},
                ],
                "forbidden": ["def (?!calculate_average\\b)\\w+", "import ", "from ", "class "],
                "principle": "Surgical & Precise Changes"
            },
            {
                "name": "temperature_converter",
                "prompt": "Write a Python function `celsius_to_fahrenheit(celsius: float) -> float` that converts Celsius to Fahrenheit. "
                          "Return ONLY the function code. Formula: F = C * 9/5 + 32.",
                "assertions": [
                    {"input": 0, "expected": 32.0},
                    {"input": 100, "expected": 212.0},
                    {"input": -40, "expected": -40.0},
                    {"input": 37, "expected": 98.6},
                ],
                "forbidden": ["def (?!celsius_to_fahrenheit\\b)\\w+", "class ", "import "],
                "principle": "Simplicity & Minimum Viable"
            },
        ]

        tests = []
        for i in range(count):
            task = tasks[i % len(tasks)]
            prompt = (
                f"Task: {task['prompt']}\n\n"
                f"Apply the dann-specs principle: '{task['principle']}'. "
                f"Return ONLY the function code in a markdown python block."
            )
            good = (f"```python\ndef {task['name']}(...):\n    # minimal implementation\n    pass\n```")

            tests.append(TestCase(
                id=f"concrete-{task['name']}-{i:03d}",
                category="concrete",
                sub_category=task["principle"],
                prompt=prompt,
                expected_behaviors=[task["principle"], "produces executable code"],
                good_response=good,
                bad_response="Here's how I would write it... [no actual code or extra functions]",
                rubric_target={"Scope Discipline": 4, "Simplicity": 4, "Verification": 4},
                concrete_assertions=task["assertions"],
                forbidden_patterns=task["forbidden"]
            ))
        return tests

    def _extract_and_verify_code(self, response: str, assertions: List[Dict],
                                  forbidden: List[str]) -> Dict:
        """Extract Python code from response, run assertions, check for forbidden patterns."""
        code = ""
        m = re.search(r'```(?:python)?\s*([\s\S]*?)```', response)
        if m:
            code = m.group(1).strip()
        else:
            lines = response.strip().split('\n')
            code_lines = []
            in_code = False
            for line in lines:
                if line.strip().startswith('def ') or in_code:
                    in_code = True
                    code_lines.append(line)
            code = '\n'.join(code_lines) if code_lines else ""

        if not code or 'def ' not in code:
            return {"score": 1.0, "passed": False,
                    "details": "no executable function found in response"}

        for pattern in forbidden:
            try:
                if re.search(pattern, code):
                    return {"score": 2.0, "passed": False,
                            "details": f"forbidden pattern found: {pattern}"}
            except re.error:
                pass

        passed = 0
        total = len(assertions)
        for assertion in assertions:
            try:
                import_fn = assertion["input"]
                expected = assertion["expected"]
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    f.write(code + f"\n\nimport json\n_result = {code.split('def ')[1].split('(')[0]}({json.dumps(import_fn)})\nprint(json.dumps(_result))\n")
                    tmp_path = f.name
                try:
                    result = subprocess.run(
                        [sys.executable, tmp_path],
                        capture_output=True, text=True, timeout=10
                    )
                    os.unlink(tmp_path)
                    if result.returncode == 0:
                        actual = json.loads(result.stdout.strip())
                        if actual == expected:
                            passed += 1
                except Exception:
                    try:
                        os.unlink(tmp_path)
                    except OSError:
                        pass
            except Exception:
                pass

        pass_rate = passed / total if total > 0 else 0
        score = 1.0 + (pass_rate * 4.0)
        return {
            "score": round(score, 1),
            "passed": score >= 4.0,
            "details": f"exec: {passed}/{total} assertions passed"
        }

    def _build_system_prompt(self, test: TestCase) -> str:
        mini_path = self.project_root / "mini" / "core.md"
        core = ""
        if mini_path.exists():
            core = mini_path.read_text().strip() + "\n\n"
        else:
            agents_path = self.project_root / "AGENTS.md"
            if agents_path.exists():
                core = agents_path.read_text()[:2000] + "\n\n---\n\n"
            else:
                core = "Follow these core rules: Think & Frame, Simplicity, Surgical, Goal-Driven+Verify, Tradeoffs. Be explicit.\n\n"

        specific = ""
        if test.category == "roles" and hasattr(test, 'sub_category'):
            role_path = self.project_root / "roles" / f"{test.sub_category}.md"
            if role_path.exists():
                specific = f"\n\nRole: {test.sub_category}\n{role_path.read_text()[:800]}\n"
            else:
                specific = f"\nYou are operating in the role of: {test.sub_category}.\n"
        elif test.category == "variants" and hasattr(test, 'sub_category'):
            var_path = self.project_root / "variants" / test.sub_category / "AGENTS.md"
            if var_path.exists():
                specific = f"\n\nVariant ({test.sub_category}):\n{var_path.read_text()[:700]}\n"

        return core + specific + "\nApply the principles above. Respond structured and be explicit."

    def score_response(self, test: TestCase, response: str) -> Dict:
        """Score a response. Uses judge LLM if available, otherwise heuristic keyword matching."""
        resp = (response or "").strip()
        if not resp or resp.startswith("LLM_ERROR") or resp.startswith("ERROR"):
            return {"score": 1.0, "passed": False, "details": "empty or error response from LLM",
                    "judge_scores": {}, "judge_justification": ""}
        if len(resp) > 10 and resp.count("/") > len(resp) * 0.6:
            return {"score": 1.0, "passed": False, "details": "garbage output from provider (slashes)",
                    "judge_scores": {}, "judge_justification": ""}

        # Concrete tests: verify code execution
        if test.concrete_assertions:
            return self._extract_and_verify_code(resp, test.concrete_assertions, test.forbidden_patterns)

        # Use judge evaluator if available
        if self.judge_evaluator:
            return self.judge_evaluator.evaluate(test, resp)

        # Heuristic fallback
        score = 1.8
        details = []
        resp_lower = resp.lower()
        words = resp.split()
        resp_len = len(words)

        has_framing = any(kw in resp_lower for kw in ["assumption", "assume", "i assume", "unknown", "clarif",
                                                        "supongo", "asum", "assumptions:"])
        if has_framing:
            score += 0.8
            details.append("framing")

        has_verify = any(kw in resp_lower for kw in ["test", "verify", "evidence", "passed", "output:", "metric",
                                                       "comprob", "verif", "prueba", "verification:"])
        if has_verify:
            score += 1.0
            details.append("verification")

        has_surgical = any(kw in resp_lower for kw in ["only", "minimal", "surgical", "just the", "no other changes",
                                                         "scoped", "solo", "minimo", "minimal change"])
        if has_surgical:
            score += 0.7
            details.append("surgical/minimal")

        if resp_len < 180 and (has_framing or has_verify or has_surgical):
            score += 0.5
            details.append("concise+structured")

        if any(kw in resp_lower for kw in ["while i'm at it", "also refactor", "extra feature", "bonus", "ademas",
                                             "unrelated"]):
            score -= 1.0
            details.append("scope creep")

        if not (has_framing or has_verify or has_surgical) and resp_len > 20:
            score = min(score, 2.4)
        if resp_len < 15 and not (has_framing or has_verify):
            score = 1.2

        score = max(1.0, min(5.0, round(score, 1)))
        passed = score >= 4.0

        return {
            "score": score, "passed": passed,
            "details": "; ".join(details) if details else (
                "terse no signals" if resp_len < 30 else "no explicit principles shown"),
            "judge_scores": {}, "judge_justification": ""
        }

    def _compute_repetition_stats(self, scores: List[float]) -> Tuple[float, float]:
        if len(scores) <= 1:
            return scores[0] if scores else 0.0, 0.0
        return statistics.mean(scores), statistics.stdev(scores)

    def run_suite(self, suite_name: str, count: int = 30) -> List[TestResult]:
        generators = {
            "core_principles": self.generate_core_principle_tests,
            "rubric_dimensions": self.generate_rubric_tests,
            "roles": self.generate_role_tests,
            "variants": self.generate_variant_tests,
            "concrete": self.generate_concrete_tests,
        }

        if suite_name not in generators:
            if suite_name == "all":
                all_results = []
                for s in generators:
                    all_results.extend(self.run_suite(s, count))
                return all_results
            raise ValueError(f"Unknown suite: {suite_name}")

        test_cases = generators[suite_name](count)
        results = []

        rep_label = f", {self.repetitions} reps each" if self.repetitions > 1 else ""
        judge_label = f", judge={self.judge_provider_name}" if self.judge_evaluator else ""
        print(f"\n=== Running suite: {suite_name} ({len(test_cases)} tests{rep_label}{judge_label}) ===")
        start_suite = time.time()

        for idx, tc in enumerate(test_cases, 1):
            rep_count = self.repetitions if self.use_real_llm else 1
            rep_scores = []
            rep_raws = []
            rep_times = []
            rep_results = []

            for rep in range(rep_count):
                rep_label = f" [rep {rep+1}/{rep_count}]" if rep_count > 1 else ""
                print(f"  [{idx}/{len(test_cases)}] {tc.id}{rep_label} ... ", end="", flush=True)
                t0 = time.time()

                if self.use_real_llm:
                    if not self.llm_client:
                        result = TestResult(
                            test_id=tc.id, category=tc.category,
                            score=1.0, passed=False,
                            details="REAL ATTEMPT FAILED: no LLM client",
                            time_seconds=0.0, prompt_system="", prompt_user=tc.prompt,
                            raw_response="", self_evaluation={}
                        )
                    else:
                        system = self._build_system_prompt(tc)
                        user = tc.prompt.split("\n\nFollow")[0] if "\n\nFollow" in tc.prompt else tc.prompt

                        if tc.category != "concrete":
                            user = user + """

Respond with explicit structure (after any thinking/reasoning):
Assumptions: ...
Plan: ...
[minimal answer here]
Verification: ...
```json
{"Framing & Assumptions": N, "Scope Discipline": N, "Simplicity": N, "Verification": N, "Tradeoffs": N, "comment": "..."}
```
Follow the core principles strictly. Keep relatively concise but complete the sections and JSON. Put the final structured response visibly (not only inside thinking)."""

                        actual = self._call_llm(system, user)
                        raw = actual or ""

                        if raw.startswith("LLM_ERROR") or raw.startswith("ERROR") or len(raw.strip()) < 3:
                            result = TestResult(
                                test_id=tc.id, category=tc.category,
                                score=1.0, passed=False,
                                details=f"REAL ATTEMPT FAILED or empty: {raw[:120]}",
                                time_seconds=time.time() - t0,
                                prompt_system=system, prompt_user=user,
                                raw_response=raw, self_evaluation={}
                            )
                        else:
                            eval_result = self.score_response(tc, raw)

                            self_eval = {}
                            if tc.category != "concrete":
                                try:
                                    fenced = re.search(r'```json\s*([\s\S]*?)\s*```', raw, re.IGNORECASE)
                                    candidate = fenced.group(1) if fenced else raw
                                    m = re.search(r'\{[\s\S]*\}', candidate)
                                    if m:
                                        parsed = json.loads(m.group(0))
                                        self_eval = {k: float(v) for k, v in parsed.items()
                                                     if isinstance(v, (int, float))}
                                        vals = [v for v in self_eval.values()]
                                        if vals and not self.judge_evaluator:
                                            self_avg = round(sum(vals) / len(vals), 1)
                                            eval_result["score"] = self_avg
                                            eval_result["passed"] = self_avg >= 4.0
                                except Exception:
                                    self_eval = {}

                            result = TestResult(
                                test_id=tc.id, category=tc.category,
                                score=eval_result["score"], passed=eval_result["passed"],
                                details=f"Real: {eval_result['details']}",
                                time_seconds=time.time() - t0,
                                prompt_system=system, prompt_user=user,
                                raw_response=raw, self_evaluation=self_eval,
                                judge_scores=eval_result.get("judge_scores", {}),
                                judge_justification=eval_result.get("judge_justification", "")
                            )
                else:
                    # Simulation mode
                    eval_result = self.score_response(tc, tc.good_response)
                    result = TestResult(
                        test_id=tc.id, category=tc.category,
                        score=eval_result["score"], passed=eval_result["passed"],
                        details=f"Sim: {eval_result['details']}",
                        time_seconds=time.time() - t0,
                        prompt_system="SIMULATED", prompt_user=tc.prompt,
                        raw_response=tc.good_response, self_evaluation={}
                    )

                rep_scores.append(result.score)
                rep_raws.append(result.raw_response or "")
                rep_times.append(result.time_seconds)
                rep_results.append(result)

                raw_preview = (result.raw_response or "").replace("\n", " ")[:80] if self.use_real_llm else ""
                extra = f" | '{raw_preview}...'" if raw_preview else ""
                print(f"{result.score:.1f} ({result.time_seconds:.1f}s){extra}")

            # Aggregate repetitions
            if rep_count > 1:
                avg_score, std_dev = self._compute_repetition_stats(rep_scores)
                base = rep_results[0]
                base.score = round(avg_score, 1)
                base.passed = avg_score >= 4.0
                base.std_dev = round(std_dev, 2)
                base.n_repetitions = rep_count
                base.repetition_scores = rep_scores
                base.time_seconds = sum(rep_times)
                base.details = (f"x{rep_count} avg={avg_score:.1f}+/-{std_dev:.2f} | " +
                                base.details.split("|", 1)[-1] if "|" in base.details else base.details)
                results.append(base)
            else:
                rep_results[0].repetition_scores = None
                results.append(rep_results[0])

            try:
                self._save_partial(results, suite_name)
            except Exception:
                pass

        print(f"--- Suite {suite_name} completed in {time.time() - start_suite:.1f}s ---")
        return results

    def _save_partial(self, results: List[TestResult], suite: str):
        results_dir = self.project_root / "tests" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        out_path = results_dir / f"{suite}_results.json"
        data = [asdict(r) for r in results]
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

    def save_results(self, results: List[TestResult], suite: str):
        results_dir = self.project_root / "tests" / "results"
        results_dir.mkdir(parents=True, exist_ok=True)
        out_path = results_dir / f"{suite}_results.json"

        data = [asdict(r) for r in results]
        with open(out_path, "w") as f:
            json.dump(data, f, indent=2)

        passed = sum(1 for r in results if r.passed)
        avg_score = sum(r.score for r in results) / len(results) if results else 0
        print(f"\n=== {suite.upper()} Results ===")
        print(f"Tests run: {len(results)}")
        print(f"Passed (score >=4): {passed} ({passed/len(results)*100:.1f}%)")
        print(f"Average score: {avg_score:.2f}")
        if self.repetitions > 1:
            avg_std = sum(r.std_dev for r in results) / len(results) if results else 0
            print(f"Repetitions: {self.repetitions} | Avg std dev: {avg_std:.2f}")
        print(f"Results saved to: {out_path}")

        if results:
            self.generate_report(suite, results)


def main():
    parser = argparse.ArgumentParser(description="dann-specs Test Suite Runner v2")
    parser.add_argument("--suite", default="all",
                        choices=["all", "core_principles", "rubric_dimensions", "roles", "variants", "concrete"])
    parser.add_argument("--count", type=int, default=30, help="Number of tests per suite")
    parser.add_argument("--real-llm", action="store_true",
                        help="Call the real local LLM instead of simulated responses")
    parser.add_argument("--config", type=Path, default=None,
                        help="Path to llm-providers.json")
    parser.add_argument("--provider", default=None,
                        help="Name of the provider to use from the config file")
    parser.add_argument("--judge-provider", default=None,
                        help="Provider name for the judge/evaluator LLM (e.g. deepseek)")
    parser.add_argument("--judge-model", default=None,
                        help="Override the judge model name")
    parser.add_argument("--no-judge", action="store_true",
                        help="Disable judge evaluator, use heuristic scoring")
    parser.add_argument("--repetitions", type=int, default=1,
                        help="Run each test N times and report mean +/- std dev")
    args = parser.parse_args()

    project_root = Path(__file__).parent.parent.parent
    workspace_root = project_root.parent

    judge_prov = None if args.no_judge else (args.judge_provider or None)

    harness = DannSpecsTestHarness(
        project_root,
        config_path=args.config,
        provider=args.provider,
        use_real_llm=args.real_llm,
        judge_provider=judge_prov,
        judge_model=args.judge_model,
        repetitions=args.repetitions
    )

    mode = "REAL LLM" if args.real_llm else "SIMULATED"
    print(f"Running dann-specs test suite ({mode}) from workspace: {workspace_root}")
    print(f"Config source: {args.config or 'auto-detected in local/'}")
    if args.provider:
        print(f"Provider: {args.provider}")
    if harness.judge_evaluator:
        print(f"Judge: {judge_prov} (model={harness.judge_model})")
    if args.repetitions > 1:
        print(f"Repetitions: {args.repetitions}")

    results = harness.run_suite(args.suite, args.count)
    harness.save_results(results, args.suite)

    if args.suite == "all":
        from collections import defaultdict
        by_suite = defaultdict(list)
        for r in results:
            by_suite[r.category].append(r)
        print("\n=== OVERALL SUMMARY ===")
        suite_order = ["core_principles", "rubric_dimensions", "roles", "variants", "concrete"]
        total_all = 0
        total_passed = 0
        total_scores = 0
        for s in suite_order:
            res = by_suite.get(s, [])
            n = len(res)
            if n:
                avg = sum(r.score for r in res) / n
                pct = sum(1 for r in res if r.passed) / n * 100
                std_info = ""
                if args.repetitions > 1:
                    avg_std = sum(r.std_dev for r in res) / n if n else 0
                    std_info = f" std={avg_std:.2f}"
                total_all += n
                total_passed += sum(1 for r in res if r.passed)
                total_scores += sum(r.score for r in res)
                print(f"  {s:25s}  {n:3d} tests  passed: {sum(1 for r in res if r.passed):3d}/{n} ({pct:.0f}%)  avg: {avg:.2f}{std_info}")
        if total_all:
            overall_avg = total_scores / total_all
            print(f"  {'TOTAL':25s}  {total_all:3d} tests  passed: {total_passed:3d}/{total_all} ({total_passed/total_all*100:.0f}%)  avg: {overall_avg:.2f}")


if __name__ == "__main__":
    main()
