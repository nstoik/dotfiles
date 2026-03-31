# Claude Code Configuration

This directory is managed by dotbot via `meta/configs/claude.yaml`. Files are symlinked into `~/.claude/`.

## Files

| Source | Destination | Purpose |
|--------|-------------|---------|
| `settings.json` | `~/.claude/settings.json` | Claude Code settings and permissions |
| `CLAUDE.md` | `~/.claude/CLAUDE.md` | Instructions loaded into every session |
| `statusline-command.sh` | `~/.claude/statusline-command.sh` | Status line command |
| `skills/` | `~/.claude/skills/` | Personal skills available across all projects |

## skills/

| Skill | Description |
|-------|-------------|
| `pr-review-fix` | Work through PR review comments interactively — fix, commit, reply with commit hash, resolve threads |

## settings.json Permissions Reference

The `allow` list pre-approves these `gh` tool patterns without prompting. Anything not listed will prompt the user for approval.

### General GitHub read access
- `gh pr view/list/checks/diff/status` — inspect PRs
- `gh issue view/list/status` — inspect issues
- `gh repo view` — inspect repo metadata
- `gh run view/list` — inspect CI runs
- `gh release view/list` — inspect releases

### `/pr-review-fix` skill
- `gh api repos/*/pulls/*/comments*` — read inline review comment threads
- `gh api repos/*/issues/*/comments*` — read general PR/issue comments
- `gh api -X POST repos/*/pulls/*/comments/*/replies*` — reply to an inline review thread with a commit hash
- `gh pr comment*` — post general PR comments (replying to non-inline comments)

> GraphQL mutations (e.g. resolving review threads) are intentionally left out so the user is prompted before threads are marked resolved.
