## Summary

Describe the problem and the smallest behavior change that solves it.

## Risk and data boundaries

- What files, processes, Hook configuration, or Multica data can this change affect?
- How does the change preserve unrelated user data?

## Verification

- [ ] `./scripts/test.sh` passes locally.
- [ ] New or changed behavior has regression coverage.
- [ ] `CHANGELOG.md` is updated under `Unreleased`.
- [ ] English and Chinese READMEs are aligned when user behavior changes.
- [ ] Code comments and docstrings are in English.
- [ ] No tokens, private rollout content, logs, or user-specific paths are included.
- [ ] `VERSION` and the plugin manifest agree if this is a release pull request.
