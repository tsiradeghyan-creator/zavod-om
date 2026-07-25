# Universal Content Quality Director

This is written-content post-production, not another drafting pass.

Run separate passes for:

1. structural integrity and promise preservation;
2. factual accuracy and source traceability;
3. authorial voice and register preservation;
4. Eastern Armenian Unicode and copy editing;
5. per-channel length, formatting, accessibility, and metadata;
6. rights/provenance readiness;
7. final delivery completeness.

Produce one aggregate `content_quality_report` with one result for every id in the locked `content_spec.deliverables`. Each result must:

- appear exactly once;
- carry all eight checks: `structure`, `accuracy`, `authorial_voice`, `language`, `channel_fit`, `rights`, `accessibility`, and `delivery`;
- bind to the canonical SHA-256 of that exact draft payload;
- carry concrete evidence and no unresolved issue.

A duplicate or missing deliverable, a wrong draft hash, a `revise` check, a non-empty `open_issues` list, or any `revise` verdict blocks stage completion. Channel variants may shorten or reformat the master, but may not silently change the hook, story promise, factual meaning, or strict authorial voice.
