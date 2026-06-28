# Design Analysis & Rationale

This document summarizes key learnings from existing agent guidance systems (as of 2026) and how they shaped dann-specs.

## Systems Analyzed
- Karpathy-inspired behavioral guidelines (concise 4 principles focused on common LLM coding failure modes)
- product-mode (product framing, scope control, tradeoffs, outcomes)
- AGENTS.md open spec (vendor-agnostic operational context used across 60k+ repos)
- Anthropic Claude Code best practices (verification loops, plan mode, context management, sub-agents, skills/hooks)
- Cline (.clinerules — version-controlled, project-specific rules)
- Continue.dev (.continue/rules/ — flexible markdown/YAML with globs)
- Cursor rules (frontmatter + alwaysApply patterns)
- Aider conventions and various personal/global AGENTS.md files

## Key Insights Incorporated
- Pure behavioral rules (Karpathy) are powerful but benefit from framing (product-mode) and operational details.
- Fragmentation across tools is real — a universal core + thin adapters reduces duplication.
- Verification is the highest-leverage addition (tests, goals, evidence).
- Context bloat hurts performance — hence the emphasis on "mini" and "when to be light".
- Domain adaptation matters: software, research, education, and infra have different verification and success signals.
- Layered context (core + variant + project-specific) works better than one giant file.
- Roles/specialists improve focus when the task has a clear persona.

## Resulting Design Choices in dann-specs
- Single source of truth in AGENTS.md (universal).
- Thin, format-native adapters in tools/.
- Variants for project types instead of one-size-fits-all.
- Explicit "mini" version for efficiency.
- Generic roles that can be composed.
- Strong emphasis on verification and surgical scope.
- Security baseline and session continuity as first-class concerns (v2.1).
- Private overrides live in local/ (never committed).

### Security (v2.1)
Secret exposure in git history is a common failure mode for AI agents. The security principles and baseline section provide concrete, actionable rules that agents can follow. The security-auditor role gives focused review capability.

### Session Continuity (v2.1)
Agents operate in discrete sessions with no persistent memory. Without a structured log, each session starts from zero context. `SESSION_LOG.md` provides a lightweight, human-readable trail that any agent or human can read at session start to understand the current state, recent decisions, and pending work.

This design aims to be practical, maintainable, and effective across both solo developers and teams using multiple AI coding tools.