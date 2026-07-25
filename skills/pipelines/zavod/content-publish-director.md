# Universal Content Publish Director

Publication is irreversible and always owner-gated, including automatic runs.

## Rules

- `draft` and `pending_review` entries may be prepared without a rights manifest and must remain non-public.
- `published` or final `exported` entries require a schema-valid, passing `rights_manifest`.
- Every final publish/export entry carries `export_path` for the exact local payload. That file must exist and match a rights row with the same resolved `artifact_path` and SHA-256. A published entry also records the URL returned by the platform.
- Every rights row must be `controlled` or a constrained `limited` use. `unknown`, `blocked`, and `legal_review` block delivery.
- Likeness and voice rows require consent identifiers. AI model rows require the terms source URL and a pinned snapshot hash.
- Close the AI disclosure decision and include label text when labeling is required.
- If C2PA status is `signed` or `verified`, the manifest file and its SHA-256 are mandatory and are checked at the checkpoint seam. A plain payload hash is evidence of integrity, not a claim of cryptographic signing.
- The owner approves the `presentation_route`; `rights_manifest` records both `approved_by` and `approved_at`, and no scheduled or direct publication occurs without that evidence.
- Schedule performance measurement for channels that expose analytics, but never optimize away the locked authorial handwriting.
