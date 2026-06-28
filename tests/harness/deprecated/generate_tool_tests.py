import json
from pathlib import Path

suites = Path("suites")

tools = ["claude", "cline", "continue", "cursor", "aider"]
conflict_tests = []
tool_tests = []

for i in range(30):
    tool = tools[i % len(tools)]
    tool_tests.append({
        "id": f"tool-{tool}-{i:03d}",
        "category": "tool_adapters",
        "tool": tool,
        "task": f"Use {tool} with dann-specs guidelines",
        "expected": "Follow format-specific rules while respecting core principles"
    })

for i in range(30):
    conflict_tests.append({
        "id": f"conflict-{i:03d}",
        "category": "conflict_resolution",
        "scenario": ["simplicity_vs_verification", "surgical_vs_goal", "framing_vs_speed"][i % 3],
        "task": f"Task with principle conflict {i}",
        "expected": "Apply hierarchy: Safety > Verification > Surgical > Simplicity"
    })

with open(suites / "tool_adapters_30.json", "w") as f:
    json.dump(tool_tests, f, indent=2)
with open(suites / "conflict_resolution_30.json", "w") as f:
    json.dump(conflict_tests, f, indent=2)

print("Added tool_adapters_30.json and conflict_resolution_30.json")
