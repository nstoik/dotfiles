---
name: pr-review-fix
description: Work through GitHub PR review comments interactively, one by one. For each comment, implement the fix, commit it, and reply to the comment with the commit hash. At the end, resolve all addressed threads. Use this skill when the user wants to address PR feedback, respond to reviewers, fix review comments, process GitHub PR comments, or work through pull request review threads systematically.
---

# PR Comments Workflow

Work through a PR's review comments one by one: read each comment, implement the fix, commit it, reply to the comment thread with the commit hash, and resolve addressed threads at the end.

## 1. Identify the PR

If the user provided a PR number or URL, use it. Otherwise:

```bash
gh pr view --json number,title,headRefName,url
```

If no open PR is found on the current branch, ask the user for a PR number.

Capture the repo owner/name:

```bash
gh repo view --json owner,name --jq '"\(.owner.login)/\(.name)"'
```

## 2. Fetch All Comments

### Inline review comments (file-level, with line references)

```bash
gh api repos/{owner}/{repo}/pulls/{pr_number}/comments \
  --paginate --slurp \
  --jq '[.[] | .[] | {id, path, line, original_line, body, user: .user.login, html_url, in_reply_to_id, diff_hunk}]'
```

Keep only top-level threads: filter out entries where `in_reply_to_id` is non-null — those are existing replies, not new threads to address.

### General PR comments (conversation tab)

```bash
gh api repos/{owner}/{repo}/issues/{pr_number}/comments \
  --paginate --slurp \
  --jq '[.[] | .[] | {id, body, user: .user.login, html_url, created_at}]'
```

Skip bot comments (user login ends in `[bot]`).

### Build the work list

Combine the two lists. Show a numbered summary to the user:

```
Found N comment(s) to address:
  1. [inline] src/foo.py:42 — @alice: "This variable name is unclear..."
  2. [inline] tests/test_bar.py:15 — @bob: "Missing edge case for empty input"
  3. [general] @alice: "Should we add a CHANGELOG entry?"
```

Ask if the user wants to work through all of them in order, or pick specific ones.

## 3. Interactive Comment Loop

For each comment in the work list:

### Display the comment

```
══════════════════════════════════════════════
Comment 1 of N  [inline]
──────────────────────────────────────────────
File:    src/foo.py, line 42
Author:  @alice
URL:     https://github.com/...

  "This variable name is unclear. Consider renaming `d` to
   something that describes what it holds."

Diff context:
  @@ -40,5 +40,5 @@
     result = []
  -  d = {}
  +  ...
══════════════════════════════════════════════
```

For inline comments, also read the relevant file section around the referenced line for additional context.

### Prompt the user

Ask: **Address this now, Skip, or Stop?** (`a` / `s` / `q`)

- **Skip**: move to the next comment, record as skipped
- **Stop**: exit the loop early, go to the summary
- **Address**: continue below

### Implement the fix

1. Read the relevant file if not already in context.
2. Analyze the comment and propose a concrete change.
3. Show the proposed diff and confirm with the user before editing.
4. Apply the fix using Edit or Write tools.

### Commit the fix

Stage only the files changed for this fix — do not use `git add .` blindly if unrelated changes exist:

```bash
git add <changed files>
git status  # confirm what's staged
git commit -m "$(cat <<'EOF'
<brief imperative summary of the fix>

Addresses review comment: <comment URL>

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
```

Capture the commit hash immediately:

```bash
git rev-parse HEAD
```

### Reply to the comment thread with the commit hash

For **inline review comments**:

```bash
gh api -X POST \
  repos/{owner}/{repo}/pulls/comments/{comment_id}/replies \
  --field body="Fixed in {commit_hash} — <one-line summary of what changed>"
```

For **general PR comments**, reply as a new comment quoting the original:

```bash
gh pr comment {pr_number} \
  --body "> <first line of original comment>

Fixed in {commit_hash} — <one-line summary of what changed>"
```

Record: `{ comment_id, commit_hash, thread_type }` for the final step.

## 4. Final Summary

After the loop, print a table:

```
╔══════════════════════════════════════════════════════╗
║  PR Comments — Session Summary                       ║
╠══════════════╦═══════════════╦═══════════════════════╣
║  Addressed   ║  Skipped      ║  Total                ║
║  3           ║  1            ║  4                    ║
╠══════════════╩═══════════════╩═══════════════════════╣
║  Commit log                                          ║
║  abc1234  Address: rename variable `d` → `data_map` ║
║  def5678  Address: add empty-input edge case test    ║
║  ghi9012  Address: add CHANGELOG entry for v1.2      ║
╚══════════════════════════════════════════════════════╝
```

## 5. Resolve Addressed Threads

For each inline comment thread that was addressed, offer to mark it resolved on GitHub. This requires GraphQL.

First, get the review thread node IDs:

```bash
gh api graphql -f query='
  query($owner: String!, $repo: String!, $pr: Int!) {
    repository(owner: $owner, name: $repo) {
      pullRequest(number: $pr) {
        reviewThreads(first: 100) {
          nodes {
            id
            isResolved
            comments(first: 1) {
              nodes { databaseId }
            }
          }
        }
      }
    }
  }
' -f owner="{owner}" -f repo="{repo}" -F pr={pr_number}
```

Match each thread's `comments.nodes[0].databaseId` against the `comment_id` values you recorded. For matching threads, resolve them:

```bash
gh api graphql -f query='
  mutation($threadId: ID!) {
    resolveReviewThread(input: {threadId: $threadId}) {
      thread { isResolved }
    }
  }
' -f threadId="{thread_node_id}"
```

Ask the user before resolving: "Resolve N addressed thread(s) on GitHub? (y/n)"

## 6. Push (optional)

Ask the user: "Push these commits to the remote branch? (y/n)"

If yes:
```bash
git push
```

## Notes

- Never force-push. If `git push` is rejected, surface the error and ask the user how to proceed.
- If a commit hook fails, investigate the cause — do not use `--no-verify`.
- Only stage files directly related to the current fix. If `git status` shows unrelated changes, confirm with the user which files to include.
- If the user rejects a proposed fix, discuss alternatives before implementing.
- Skip comments that appear to already have a reply from the current user, unless the user explicitly asks to re-address them.
