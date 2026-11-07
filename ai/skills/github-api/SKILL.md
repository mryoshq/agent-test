---
name: github-api
description: Call the GitHub REST API with curl for agent-test. Covers reading PRs and issues, opening a PR, commenting and posting a commit status, with JSON built by python3 (jq is not installed). Use whenever a task needs the GitHub API.
---

# github-api

Rules:
- `jq` is not installed. Build and parse JSON with python3.
- Never put `$GITHUB_TOKEN` in a file, a URL or any output.
- `/tmp` is shared with other sessions, each running as a different user. Keep every file in your own folder `$TMPDIR` (the first shared line), never directly in `/tmp`.
- Shells do not keep variables between commands: start every command with the shared lines.
- If a command fails (for example "PRIVATE TMP FAILED" or "Permission denied"), stop and report it. Never switch to another path, and never reuse a file you did not write in this session.

Shared lines:
```sh
export TMPDIR="/tmp/agent-$(id -u)"; mkdir -p -m 700 "$TMPDIR" && [ -O "$TMPDIR" ] || { echo "PRIVATE TMP FAILED"; exit 1; }
GH=(-s --fail-with-body -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json")
API=https://api.github.com/repos/$REPO_SLUG
```

Read a PR or an issue:
```sh
curl "${GH[@]}" $API/pulls/<n> > "$TMPDIR/pr.json"
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(d["head"]["sha"], d["head"]["ref"], d["title"])' "$TMPDIR/pr.json"
python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["head"]["sha"], end="")' "$TMPDIR/pr.json" > "$TMPDIR/head_sha"
curl "${GH[@]}" $API/issues/<k> > "$TMPDIR/issue.json"
```

Open a PR (coder):
```sh
python3 -c 'import json,sys; print(json.dumps({"title": sys.argv[1], "head": sys.argv[2], "base": "main", "body": sys.argv[3]}))' \
  "<title>" "<branch>" "Resolves #<issue>" > "$TMPDIR/pr_body.json"
curl "${GH[@]}" -X POST $API/pulls -d @"$TMPDIR/pr_body.json" > "$TMPDIR/pr_out.json"
python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["html_url"])' "$TMPDIR/pr_out.json"
```

Comment on a PR or an issue (write the text to `$TMPDIR/comment.md` first):
```sh
python3 -c 'import json,sys; print(json.dumps({"body": sys.stdin.read()}))' < "$TMPDIR/comment.md" > "$TMPDIR/comment.json"
curl "${GH[@]}" -X POST $API/issues/<n>/comments -d @"$TMPDIR/comment.json" > /dev/null
```

Commit status (reviewer only; the description can be at most 140 characters):
```sh
python3 -c 'import json,sys; print(json.dumps({"state": sys.argv[1], "context": "agent-review", "description": sys.argv[2][:140]}))' \
  "<success|failure>" "<summary>" > "$TMPDIR/status.json"
curl "${GH[@]}" -X POST "$API/statuses/$(cat "$TMPDIR/head_sha")" -d @"$TMPDIR/status.json" > "$TMPDIR/status_out.json" \
  || { echo "STATUS POST FAILED"; cat "$TMPDIR/status_out.json"; }
curl "${GH[@]}" "$API/commits/$(cat "$TMPDIR/head_sha")/statuses" > "$TMPDIR/statuses.json"
python3 -c 'import json,sys; s=[x for x in json.load(open(sys.argv[1])) if x["context"]=="agent-review"]; print("agent-review status:", s[0]["state"] if s else "MISSING")' "$TMPDIR/statuses.json"
```
Never type a SHA by hand: always use `$(cat "$TMPDIR/head_sha")`, written from the API above in this session.
If the read-back prints MISSING, the status did not land: say so in your reply (REVIEW_RESULT: error).
