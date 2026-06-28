---
name: dann-specs
description: Unified behavioral guidelines for AI coding agents. Combines Karpathy principles, product-mode thinking, AGENTS.md standards, and Anthropic best practices. Use when writing, reviewing, or refactoring code with any agent.
license: MIT
---

# Dann-Specs Guidelines

**Read AGENTS.md first.** This skill loads the unified principles.

Behavioral guidelines to reduce common LLM coding mistakes and improve problem framing.

**Core fusion:**
- Karpathy’s 4 principles (Think Before Coding, Simplicity First, Surgical Changes, Goal-Driven Execution)
- Product-mode’s 7 principles (problem framing, tradeoffs, outcomes)
- AGENTS.md operational standards
- Anthropic agentic best practices (verification, sub-agents, context hygiene)

See the full `AGENTS.md` and `CLAUDE.md` in this repository for the complete rules.

**Tradeoff:** Bias toward rigor and verification over raw speed. For trivial tasks use judgment.

## Quick Reference

1. **Think + Frame** — State assumptions. Understand the real problem first.
2. **Simplicity + Minimum Viable** — Smallest correct change. No speculative features.
3. **Surgical** — Touch only what was asked. Match existing style.
4. **Goal-Driven + Verification** — Turn tasks into testable goals. Provide evidence.
5. **Tradeoffs & Logging** — Name the costs. Log important decisions.
6. **Agentic Workflow** — Explore/Plan → Implement → Verify. Use sub-agents when needed.

Apply these in every coding, refactoring, or review task.