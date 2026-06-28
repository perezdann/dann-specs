#!/usr/bin/env python3
"""Generate detailed static test case files for dann-specs."""
import json
from pathlib import Path

def main():
    suites_dir = Path("suites")
    suites_dir.mkdir(exist_ok=True)

    # 30 detailed core principle tests
    core_tests = []
    principles = [
        "Think & Frame Before Acting",
        "Simplicity & Minimum Viable",
        "Surgical & Precise Changes",
        "Goal-Driven with Verification",
        "Surface Tradeoffs & Log Decisions",
        "Verification-First Workflow",
        "Agentic Workflow Discipline"
    ]
    
    for i in range(30):
        p = principles[i % len(principles)]
        core_tests.append({
            "id": f"core-{i:03d}",
            "category": "core_principles",
            "principle": p,
            "task": f"Task {i}: Implement feature related to {p.lower()}",
            "prompt": f"Implement a feature. Pay special attention to the principle of {p}.",
            "must_do": [
                "State assumptions explicitly",
                "Define verifiable success criteria",
                "Make only minimal necessary changes",
                "Show evidence of verification"
            ],
            "must_avoid": ["over-engineering", "scope creep", "vague success claims"]
        })

    with open(suites_dir / "core_principles_30.json", "w") as f:
        json.dump(core_tests, f, indent=2)

    # 30 rubric tests
    rubric_tests = []
    dims = ["Framing & Assumptions", "Scope Discipline", "Simplicity", "Verification", "Tradeoffs"]
    for i in range(30):
        d = dims[i % len(dims)]
        rubric_tests.append({
            "id": f"rubric-{i:03d}",
            "category": "rubric",
            "dimension": d,
            "task": f"Task for {d}",
            "expected_min_score": 4
        })
    with open(suites_dir / "rubric_30.json", "w") as f:
        json.dump(rubric_tests, f, indent=2)

    # Roles sample (spread across 13 roles)
    roles = ["physician", "lawyer", "accountant", "nurse", "mechanic", 
             "electronics-technician", "seamstress", "graphic-designer", "architect",
             "domain-specialist", "researcher", "educator", "reviewer"]
    role_tests = []
    for i in range(30):
        role = roles[i % len(roles)]
        role_tests.append({
            "id": f"role-{role}-{i:03d}",
            "category": "roles",
            "role": role,
            "task": f"Perform a task typical for a {role}",
            "expected_behaviors": ["domain-specific framing", "appropriate verification"]
        })
    with open(suites_dir / "roles_30.json", "w") as f:
        json.dump(role_tests, f, indent=2)

    print("Generated 90+ static test case files in suites/")
    print("Files created:")
    for f in sorted(suites_dir.glob("*.json")):
        print(f"  - {f.name}")

if __name__ == "__main__":
    main()
    # Workflow tests (plan, verify, surgical, etc.)
    workflow_tests = []
    for i in range(30):
        workflow_tests.append({
            "id": f"workflow-{i:03d}",
            "category": "workflow",
            "focus": ["plan", "verify", "surgical", "subagent"][i % 4],
            "task": f"Complex multi-step task {i}",
            "expected": "Use plan mode, define verification, stay surgical"
        })
    with open(suites_dir / "workflow_30.json", "w") as f:
        json.dump(workflow_tests, f, indent=2)
    print("Added workflow_30.json")
