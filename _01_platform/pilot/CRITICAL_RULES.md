# Critical Rules

These rules govern all work within the `pilot/` package. They are non-negotiable unless explicitly overridden by the owner.

---

1. **Do not start by rewriting the runtime.** The pilot package is a specification and governance layer, not a runtime replacement. Existing Upsilon behavior is preserved until the architecture is reviewed and approved.

2. **Do not build signup/auth/billing/customer portals.** The pilot package defines pilot architecture, not customer onboarding infrastructure.

3. **Do not equate self-service with pilot legitimacy.** A pilot is a bounded, instrumented evaluation. Self-service access is a separate concern.

4. **Do not turn this into generic project-management infrastructure.** The pilot package is specific to Upsilon Enterprise Pilots. Generic PM tooling is out of scope.

5. **Do not invent functionality that does not exist.** Every implementation claim must cite actual repository evidence — files, functions, tests, or runtime behavior.

6. **Distinguish synthetic demo evidence from real-customer capability.** The ACME-001 demo uses synthetic data. Synthetic results must never be represented as customer proof or production evidence.

7. **Preserve existing scoring and metric definitions.** The pilot package does not override existing measurement/scoring definitions unless an explicit conflict is found, documented, and approved.

8. **Treat pilot success criteria as locked before measurement whenever possible.** Success criteria defined at charter time should not shift to accommodate results.

9. **Treat every pilot as terminating in a decision.** No indefinite pilot state. Every pilot ends in STOP, EXTEND, EXPAND, or DEPLOY.

10. **Prefer integration of existing Upsilon components over duplication.** If a capability already exists, bind it to the pilot lifecycle rather than rebuilding it.

11. **ACME-001 should expose gaps rather than conceal them.** The reference pilot's purpose is to reveal where the protocol cannot currently be completed, not to paper over missing pieces.

12. **Do not silently edit archived material.** Archive is provenance-preserving. Changes to archived content require explicit documentation.
