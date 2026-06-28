# Software Development Variant

Core principles from root AGENTS.md apply fully.

## Additional Emphasis
- Write or update tests for changed behavior.
- Prefer existing patterns in the codebase.
- Run linting/type-checking as part of verification.
- Keep changes reviewable (small, focused diffs).
- Never commit secrets or credentials. Use `.env` files (gitignored) or environment variables.
- Validate all inputs. Sanitize user-facing output.
- Use pre-commit hooks: `detect-private-key`, `detect-secrets`, `lint-staged`.

---

**English** | [Español](AGENTS.es.md)
