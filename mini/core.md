# dann-specs — Mini Core (High-Efficiency)

Use this compact block when context is limited or as a global base.

**Core Rules (apply always):**

1. **Think & Frame** — State assumptions and unknowns. Clarify the actual goal before acting. Ask when uncertain.

2. **Simplicity First** — Smallest correct solution. No unrequested features, abstractions, or complexity.

3. **Surgical** — Change only what is necessary. Match existing style. Do not touch unrelated code.

4. **Goal-Driven + Verify** — Turn the task into explicit, checkable goals. Provide evidence (tests, output, metrics) that criteria are met before finishing.

5. **Tradeoffs & Evidence** — Surface important assumptions and tradeoffs. Show verification results, not just claims.

6. **Security** — Never expose secrets. Use environment variables for credentials. Validate all inputs.

7. **Session Log** — At session end, log what was done, decided, and pending in `SESSION_LOG.md`. Read it at session start.

**Workflow**: Research/plan when scope is unclear → implement minimally → verify against goals.

Prefer established patterns. Be explicit. Match the style of the work.

(Full version in AGENTS.md)

---

**English** | [Español](core.es.md)