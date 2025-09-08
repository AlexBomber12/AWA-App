## Summary
- [ ] cloud-only workflow: unit then integration
- [ ] artifacts reviewed (compose-logs.txt, compose-ps.txt)
- [ ] Run Summary checked
- [ ] coverage thresholds not lowered
- [ ] If CI failed, read the AI hints in the failure comment and reply `@codex review`.

## Test Plan
- [ ] `pytest -m "not integration"`
- [ ] `npm test` (web)
- [ ] `npm run build` (webapp)
- [ ] `pytest -m integration`

_On failure, read the PR comment with the log tail and comment `@codex review` to request an AI review._
