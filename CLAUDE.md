# CLAUDE.md

## Coding Agent

### The GitHub token dies at minute 60 (push early, re-mint to continue)

The GitHub App token a session starts with (`GITHUB_TOKEN`/`GH_TOKEN` in the
session environment, and embedded in the origin remote URL) expires exactly 60
minutes after the Run Claude Code step starts. The session keeps running, but
`git push` fails, `gh` fails, and the MCP tool that updates the progress
comment fails, all with 401, so from the outside the session goes silent while
finished work stops landing.

- Push and update the tracking comment early and often. Treat minute 50 as the
  deadline for anything that must reach GitHub, in case recovery fails.
- At the first 401 from a push or `gh` call (or proactively around minute 55),
  run `python scripts/refresh_github_app_token.py`. It re-runs the action's
  own OIDC exchange, saves a fresh one-hour token to `/tmp/.ghtok` (mode
  0600), and re-points the origin remote at it, so plain `git push` works
  again. Validated live on a 125 minute session that re-minted hourly.
- `gh` keeps reading the dead token from the environment, so prefix each call:
  `GH_TOKEN=$(cat /tmp/.ghtok) gh ...`. Separately, `DEFAULT_WORKFLOW_TOKEN`
  is a distinct token that lasts the whole job and works for reads at any age.
- The MCP comment tool cannot be re-keyed mid-session. After a re-mint, update
  the tracking comment over REST instead: write the body to a file and run
  `GH_TOKEN=$(cat /tmp/.ghtok) gh api -X PATCH
  repos/$GITHUB_REPOSITORY/issues/comments/<comment-id> -F body=@that-file`.
- A re-minted token also lives one hour, so re-run the script each hour it is
  needed. Never echo, log, or commit a token value; the script prints only
  statuses and lengths.
