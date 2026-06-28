# dann-specs

**Universal, tool-agnostic behavioral specification for AI agents.**

A professional synthesis of the strongest patterns from major agent guidance systems —
behavioral principles, framing discipline, operational standards, and verification-first
workflows. Designed to be the single source of truth across coding agents, research tools,
education platforms, and knowledge work.

[![License: GPL-3.0](https://img.shields.io/badge/License-GPL--3.0-blue.svg)](LICENSE)
[![Validate Spec](https://github.com/perezdann/dann-specs/actions/workflows/validate.yml/badge.svg)](https://github.com/perezdann/dann-specs/actions/workflows/validate.yml)

## Philosophy

The most effective agent instructions combine:

1. **Clear behavioral rules** — how the agent should think and act
2. **Operational context** — what the agent needs to know about the environment
3. **Verification discipline** — how success is measured
4. **Adaptability** — different modes for different project types

dann-specs delivers all four in a clean, version-controllable package.

## Quick Start

Pick your integration level:

### Level 1: Drop-in (10 seconds)
```bash
curl -O https://raw.githubusercontent.com/perezdann/dann-specs/main/project/AGENTS.md
# Commit AGENTS.md. Your LLM reads it from context. No tooling needed.
```

### Level 2: With evaluation (2 minutes)
```bash
curl -O https://raw.githubusercontent.com/perezdann/dann-specs/main/project/AGENTS.md
pip install llm-behavioral-eval
behavioral-eval --spec . --suite core_principles --count 15 --real-llm --provider ollama
# Verifies your model actually follows the spec.
```

### Level 3: Full profile (5 minutes)
```bash
git clone https://github.com/perezdann/dann-specs.git vendor/dann-specs
cp vendor/dann-specs/project/{AGENTS.md,CLAUDE.md,eval-profile.json} .
cp -r vendor/dann-specs/project/{mini,roles,variants} .
behavioral-eval --spec . --suite all --real-llm --judge-provider deepseek
# Complete evaluation with LLM judge, 5 categories, 95% CIs.
```

## Core Principles

1. **Think & Frame Before Acting** — State assumptions and unknowns. Clarify goals.
2. **Simplicity & Minimum Viable** — Smallest correct solution. No unrequested features.
3. **Surgical & Precise Changes** — Modify only what's necessary. Match existing style.
4. **Goal-Driven with Verification** — Convert requests into explicit, verifiable goals.
5. **Surface Tradeoffs & Log Decisions** — Make assumptions, constraints, tradeoffs visible.
6. **Verification-First Workflow** — Tests, linters, builds as primary signals.
7. **Agentic Workflow Discipline** — Research → Plan → Implement → Verify.

## Structure

```
project/
├── AGENTS.md                ← Main specification (universal)
├── CLAUDE.md                ← Claude Code entry point
├── evaluation-rubric.md     ← Self-evaluation dimensions (1-5)
├── eval-profile.json        ← Configuration for llm-behavioral-eval engine
├── mini/core.md             ← Compact version (<200 words, for tight context)
├── roles/                   ← 13 specialist personas
│   ├── physician.md, lawyer.md, accountant.md, nurse.md
│   ├── mechanic.md, electronics-technician.md, seamstress.md
│   ├── graphic-designer.md, architect.md, domain-specialist.md
│   ├── researcher.md, educator.md, reviewer.md
├── variants/                ← 7 domain-specific variants
│   ├── software-development/, infra-devops/, research-knowledge/
│   ├── education-courses/, product-management/, data-analysis/
│   └── professional-services/
├── tools/                   ← Ready-to-use adapters
│   ├── continue/.continue/rules/dann-specs.md
│   ├── cursor/.cursor/rules/dann-specs.mdc
│   ├── cline/.clinerules, aider/CONVENTIONS.md
│   └── universal/AGENTS.md
├── tests/                   ← Test harness (legacy, superseded by llm-behavioral-eval)
├── reports/                 ← Community test results
├── LICENSE                  ← GPL-3.0
└── CHANGELOG.md
```

## Roles

13 predefined specialist personas. Each extends core principles with domain-specific behavior:

| Role | Domain |
|---|---|
| physician | Clinical reasoning, diagnosis, treatment planning |
| lawyer | Legal analysis, contract review, advisory |
| accountant | Bookkeeping, financial reporting, tax, audits |
| nurse | Patient care, monitoring, documentation |
| mechanic | Vehicle diagnostics, repair procedures |
| electronics-technician | Circuit analysis, component repair |
| seamstress | Pattern design, garment construction |
| graphic-designer | Visual composition, brand identity |
| architect | Structural design, building systems |
| domain-specialist | Expert consultation in any field |
| researcher | Literature review, methodology, findings |
| educator | Course design, pedagogy, assessment |
| reviewer | Code/structure review, feedback |

## Variants

7 domain-specific extensions that adapt core principles:

| Variant | Emphasis |
|---|---|
| software-development | Write/update tests, prefer existing patterns, run linting |
| infra-devops | Infrastructure as code, reproducibility, rollback plans |
| research-knowledge | Clarity, reproducibility, domain-appropriate verification |
| education-courses | Pedagogical structure, assessment design, accessibility |
| product-management | User stories, acceptance criteria, stakeholder tradeoffs |
| data-analysis | Data provenance, statistical validity, visualization |
| professional-services | Client communication, deliverable structure, billing scope |

## Evaluation

dann-specs is evaluated using [llm-behavioral-eval](https://github.com/perezdann/llm-behavioral-eval),
a spec-agnostic evaluation engine. The `eval-profile.json` configures 5 test suites:

| Suite | Tests | Scoring |
|---|---|---|
| core_principles | 20 | LLM Judge or heuristic |
| rubric_dimensions | 40 | LLM Judge or heuristic |
| roles | 40 | LLM Judge or heuristic |
| variants | 25 | LLM Judge or heuristic |
| concrete | 30 (stratified) | Code execution + assertions |

### Run evaluation

```bash
pip install llm-behavioral-eval

# Simulated (fast, no LLM calls)
behavioral-eval --spec ./project --suite all

# Real LLM with judge
behavioral-eval --spec ./project --suite all --real-llm \
  --provider llama-home --judge-provider deepseek

# Measure consistency
behavioral-eval --spec ./project --suite all --real-llm --repetitions 3
```

## Supported Tools

- **AGENTS.md** — Universal standard (all tools)
- **Claude Code** → `CLAUDE.md`
- **Continue.dev** → `.continue/rules/dann-specs.md`
- **Cursor** → `.cursor/rules/dann-specs.mdc`
- **Cline** → `.clinerules`
- **Aider** → `CONVENTIONS.md`
- **Kilo Code** — Native AGENTS.md support

## Version Control

Fully automated semantic versioning on push to `main` via
[python-semantic-release](https://python-semantic-release.readthedocs.io/):

```bash
cz commit  # interactive conventional commit
git push   # CI auto-releases: bump version, update CHANGELOG, create GitHub Release
```

| Commit prefix | Bump |
|---|---|
| `feat:` | MINOR |
| `fix:` | PATCH |
| `BREAKING CHANGE:` | MAJOR |

- Tags: v1.0.0 (initial spec), v2.0.0 (engine integration + eval-profile)

## Contributing

1. Fork the repository
2. Edit AGENTS.md, roles, or variants
3. Run evaluation to verify: `behavioral-eval --spec ./project --suite all --real-llm`
4. Submit a PR with your report data in `reports/`

Community test data improves the specification empirically.

## License

GPL-3.0. See [LICENSE](LICENSE).

---

**English** | [Español](README.es.md)
