# Changelog

All notable changes to dann-specs will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [2.1.0] - 2026-06-27

### Added
- Principle #7: Security-Aware Development (secrets, input validation, least privilege)
- Principle #8: Session Continuity & Audit Trail (SESSION_LOG.md)
- Security Baseline section with concrete rules (secrets, input validation, dependencies, pre-commit)
- Session Continuity section with log entry format and discovery rules
- Security-Auditor role for focused security reviews
- Security dimension in evaluation rubric
- `SESSION_LOG.md` template for new projects

### Changed
- Conflict Resolution Hierarchy: Security-Aware Development elevated to #2 priority
- Software-development variant extended with security practices (secrets, validation, pre-commit hooks)
- Reviewer role enhanced with secret scanning checks
- Mini core compact version includes security + session log principles
- eval-profile.json updated with new principles, dimensions, and roles
- docs/analysis.md documents rationale for security + session continuity

## [2.0.0] - 2026-06-27

### Added
- `eval-profile.json` for llm-behavioral-eval engine integration
- Automated test suite: core_principles, rubric_dimensions, roles, variants, concrete
- LLM judge evaluator scoring with per-dimension analysis
- Concrete code execution tests with assertion verification
- Statistical reporting with 95% confidence intervals
- Heatmap generation for dimension-level score analysis
- A/B Arena mode for head-to-head model comparison

### Changed
- License switched from MIT to GPL-3.0
- README rewritten with engine usage documentation
- Test harness moved to `deprecated/` in favor of llm-behavioral-eval engine

### Fixed
- `.gitignore` pattern corrected to track example provider config
- Removed per-test report generation bug (was generating 300+ incremental reports)

## [1.0.0] - 2026-06-26

### Added
- Initial specification: AGENTS.md, CLAUDE.md, evaluation-rubric.md
- 7 core behavioral principles
- 13 specialist role definitions
- 7 domain variant specifications
- Mini core for context-constrained environments
- Tool adapters: Continue.dev, Cursor, Cline, Aider, universal
- Community test harness with simulated and real-LLM modes
- Report generation system (JSON + Markdown)

[2.0.0]: https://github.com/perezdann/dann-specs/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/perezdann/dann-specs/releases/tag/v1.0.0
