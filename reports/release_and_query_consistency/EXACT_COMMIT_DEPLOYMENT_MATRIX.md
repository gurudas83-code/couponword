# Exact commit and deployment matrix

Audit baseline: local `HEAD 78553b1a9eb895f417eea869af01e987d93503bb`,
`origin/main 2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`, branch `main`.
No push or deployment was run.

| Check | Result |
|---|---|
| Local/remote ancestry | Local is ahead by 6, behind by 0 |
| 42 historical commits | Exact on `origin/main` (`5167712..origin/main` = 42; `git cherry` all `+`) |
| Current eight commits | Six pre-existing integration commits plus the semantic-signature and exact-model corrections; all local-only and unpushed |
| Worktree | Dirty runtime JSON, caches, backups, ZIP and audit files preserved |

The six pre-existing commits and the two scoped query-consistency corrections
are listed in `RELEASE_MANIFEST_AND_PENDING_ACTIONS.md`. The 42-commit
historical release is therefore present on GitHub, while these eight newer
commits are not.

## Deployment surfaces

- `.github/workflows/public-pages-artifact.yml` contains `workflow_dispatch`,
  the allow-listed artifact builder and `actions/deploy-pages@v4`. No workflow
  run or live revision was verified here.
- The owner's prior dashboard confirmation says Pages source is GitHub Actions;
  live artifact contents and HTTP exclusion remain unverified in this run.
- The local builder excludes `admin.html` and internal files; a live 404 is not
  claimed.
- `app.js` points to `https://couponword.onrender.com/api/recommend`.
  Render revision, backend data and frontend/API live parity are UNKNOWN.
- Durable T5 Pro evidence/registry/offer records remain in preserved dirty
  local data and are not part of a pushed release.
