# Releasing

Releases use Semantic Versioning and immutable Git tags.

1. Create a release branch and update `VERSION`, the plugin manifest version,
   both root READMEs when commands changed, and `CHANGELOG.md`.
2. Run `./scripts/test.sh`.
3. Run `./scripts/smoke-install.sh .` against the local marketplace.
4. Open a pull request and obtain review for behavior-changing releases.
5. Merge to `main`, create an annotated `vX.Y.Z` tag, and push the tag.
6. Create a GitHub Release from the tag.
7. In a clean temporary Codex home, run:

   ```bash
   codex plugin marketplace add zhongwangquan/multica-agent-sync --ref vX.Y.Z
   codex plugin add multica-codex-sync@multica-agent-sync
   ```

8. Confirm the installed manifest version and repeat the manual Hook Trust test
   in Codex Desktop.

Never move or replace an existing release tag. Security fixes receive a new
version and release notes.
