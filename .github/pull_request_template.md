## Summary
- [ ] cloud-only workflow: unit then integration
- [ ] artifacts reviewed (compose-logs.txt, compose-ps.txt)
- [ ] Run Summary checked
- [ ] coverage thresholds not lowered

## Test Plan
- [ ] `pytest -m "not integration"`
- [ ] `npm test` (web)
- [ ] `npm run build` (webapp)
- [ ] `pytest -m integration`

_On failure, read the PR comment with the log tail and comment `@codex review` to request an AI review._
