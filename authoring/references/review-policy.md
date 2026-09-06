# Review Policy

Review only the axes that can affect the requested outcome; use these as prompts rather than a checklist that every change must satisfy:

1. Spec: every approved requirement and non-goal is accounted for.
2. Standards: repository rules, naming, error handling, and tests are followed.
3. Maintainability: complexity, duplication, fixtures, and docs remain proportional.
4. Architecture: touched boundaries have clear ownership and credible test seams.
5. Diagnostics: operator-visible state and failures are actionable when runtime behavior is involved.

High-severity findings block completion when they affect an accepted requirement, safety boundary, or required evidence. Unrun Live or Eval checks are reported as unverified, not disguised as failures or passes.
