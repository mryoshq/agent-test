---
name: github-api
description: Call the GitHub REST API with curl for agent-test. Covers reading PRs and issues, opening a PR, commenting and posting a commit status, with JSON built by python3 (jq is not installed). Use whenever a task needs the GitHub API.
---

# github-api

Rules:
- `jq` is not installed. Build and parse JSON with python3.
- Never put `$GITHUB_TOKEN` in a file, a URL or any output.

Shared header:
```sh
GH=(-s --fail-with-body -H "Authorization: Bearer $GITHUB_TOKEN" -H "Accept: application/vnd.github+json")
API=https://api.github.com/repos/$REPO_SLUG
```

Read a PR or an issue:
```sh
curl "${GH[@]}" $API/pulls/<n> > /tmp/pr.json
python3 -c 'import json; d=json.load(open("/tmp/pr.json")); print(d["head"]["sha"], d["head"]["ref"], d["title"])'
python3 -c 'import json; print(json.load(open("/tmp/pr.json"))["head"]["sha"], end="")' > /tmp/head_sha
curl "${GH[@]}" $API/issues/<k> > /tmp/issue.json
```

Open a PR (coder):
```sh
python3 -c 'import json,sys; print(json.dumps({"title": sys.argv[1], "head": sys.argv[2], "base": "main", "body": sys.argv[3]}))' \
  "<title>" "<branch>" "Resolves #<issue>" > /tmp/pr_body.json
curl "${GH[@]}" -X POST $API/pulls -d @/tmp/pr_body.json > /tmp/pr_out.json
python3 -c 'import json; print(json.load(open("/tmp/pr_out.json"))["html_url"])'
```

Comment on a PR or an issue:
```sh
python3 -c 'import json,sys; print(json.dumps({"body": sys.stdin.read()}))' < /tmp/comment.md > /tmp/comment.json
curl "${GH[@]}" -X POST $API/issues/<n>/comments -d @/tmp/comment.json > /dev/null
```

Commit status (reviewer only; the description can be at most 140 characters):
```sh
python3 -c 'import json,sys; print(json.dumps({"state": sys.argv[1], "context": "agent-review", "description": sys.argv[2][:140]}))' \
  "<success|failure>" "<summary>" > /tmp/status.json
curl "${GH[@]}" -X POST "$API/statuses/$(cat /tmp/head_sha)" -d @/tmp/status.json > /tmp/status_out.json \
  || { echo "STATUS POST FAILED"; cat /tmp/status_out.json; }
curl "${GH[@]}" "$API/commits/$(cat /tmp/head_sha)/statuses" > /tmp/statuses.json
python3 -c 'import json; s=[x for x in json.load(open("/tmp/statuses.json")) if x["context"]=="agent-review"]; print("agent-review status:", s[0]["state"] if s else "MISSING")'
```
Never type a SHA by hand: always use `$(cat /tmp/head_sha)`, written from the API above.
If the read-back prints MISSING, the status did not land: say so in your reply (REVIEW_RESULT: error).
