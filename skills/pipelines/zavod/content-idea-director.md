# Universal Content Idea Director

Use this director only for `zavod-content`. Read `ZAVODOM.md`,
`skills/zavod-craft/SKILL.md`, `idea-lab.md`, and `production-protocol.md` first.

## Contract

1. Convert the request into a schema-valid `content_spec`; never squeeze text into a video brief.
2. Run `lib.content_router.route_content`. If the route is not `zavod-content`, stop and use the returned pipeline.
3. Lock `run_mode` as `supervised` or `automatic`; copy the same value to `content_spec.automation_mode`.
4. Lock `engine_lock` to `{engine: none, compose_runtime: none}`.
5. Produce `creative_identity` separately from visual branding:
   - `neutral`: no named authorial profile;
   - `reference`: profile guides drafting, report is advisory;
   - `strict`: profile and register are binding, and the script stage cannot close without a verified report.
6. For Ani Maghakyan's Armenian screenplay handwriting, use `maghakian-script-v1`. Do not activate colors, fonts, or a visual pack unless the owner requests them.
7. Offer at least three materially different concepts and record the selection in `decision_log`.

## Exit evidence

- `brief`, `content_spec`, `creative_identity`, `decision_log`, `production_ladder`, `run_mode`, `engine_lock`, and full `bench_report`.
- Every deliverable names its target length and acceptance criteria.
- In supervised mode, freeze after the idea report. In automatic mode, continue only through draft-safe stages.
