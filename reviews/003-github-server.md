# Decision Record 003: GitHub MCP Server (official)

| | |
|---|---|
| Server and publisher | `github/github-mcp-server`, GitHub, Inc., MIT licence, written in Go |
| Version or commit hash | Release tag v2.0.2, commit `eb47a99ddb866ca2b8a162920e6bda9521f33ebb` |
| Source and date reviewed | Source at that tag, README, `docs/` and workflows, 14 October 2026 |
| Reviewer | Bill |
| Intended use case | A coding assistant working with a team's GitHub repositories, local server, default toolsets, a personal access token |
| Verdict | **Reject in its default configuration. Approve with conditions only under the hardened profile in section 5.** |

## 1. Scope and evidence

- Reviewed: README and `docs/` (scope filtering, policies and governance, server configuration); source for `delete_repository`, token scope filtering and logging flags; the 128 tool definitions; scanner output; the image signing step in `.github/workflows/docker-publish.yml`.
- Tool list provenance: **not a live `tools/list`**. The Go build was blocked in my environment (module proxy unreachable), so `reviews/github-server/manifest.json` is built from the project's own test snapshots in `pkg/github/__toolsnaps__/`, which its tests compare against the code. 13 alternate-variant snapshot files were excluded to avoid duplicate names. Output schemas were removed. A reviewer with network access should repeat this with a live call.
- Not reviewed, and why: the hosted remote server at `api.githubcopilot.com` (a different trust model, run by GitHub); the 37 direct Go dependencies (no vulnerability scan); the Docker image signature (I read the signing step but did not verify a signature); live behaviour against a real token, so the read-only, lockdown and scope-filter claims are from documentation and source only.
- Other servers expected in the same session: none assumed. See section 8 for why this matters here.

## 2. Scanner output

```
Tools scanned: 128   Findings: 547
  Permissions and Scope [HG]: at least 2  (50 findings)
  Prompt Injection Exposure [HG]: at least 2  (1 finding: reads outside content and has write tools)
  Tool Integrity and Supply Chain [HG]: at least 2  (1 finding: one 1546-character parameter description)
  Output Handling: at least 1  (495 findings)
Draft verdict: NOT DECIDED
```

Count by root cause, not by line: 361 unbounded-string findings are one root cause (open input schemas), and 126 more are another (no `additionalProperties: false`). The ones that matter: 70 write tools, 13 annotated destructive (including `delete_file` and `delete_repository`), and the ingest-plus-write hint.

False positives found on this run, both fixed in the scanner (see section 8):
- The `query` parameter of the eight search tools was read as a raw SQL string (draft Output Handling 3). GitHub search queries are search expressions. The rule now scores SQL strings at 3 and free-text queries at 1.
- `get_commit` was read as a state-changing tool because "commit" is on the write word list. A read verb at the start of a tool name now wins.

The scanner also under-scores. It cannot see that `delete_repository` demands a typed confirmation (good), nor that a classic token with the `repo` scope reaches every repository the user owns (bad).

## 3. Scores

Two columns, because the answer depends on how the server is run. "Default" is the intended use case above. "Hardened" applies the conditions in section 5.

| # | Criterion | Hard gate | Default | Hardened | Evidence |
|---|---|---|---|---|---|
| 1 | Permissions and Scope | Yes | 3 | 2 | 128 tools: 58 read-only, 70 write, 13 destructive. The default toolsets (`context`, `repos`, `issues`, `pull_requests`, `users`) include file writes, pushes, merges and deletes. With a classic token the reach is every repository the user can touch. Strong controls exist: `--read-only`, per-toolset and per-tool allow lists, an exclude list, classic-token scope filtering, and `delete_repository` requires typing the repository name through an elicitation prompt. |
| 2 | Authentication and Token Handling | Yes | 2 | 1 | Local use needs a long-lived static personal access token in an environment variable or config file (README recommends `chmod 600`). Scope filtering works only for classic tokens; fine-grained and app tokens "show all tools". OAuth with scope challenges exists (`--oauth-client-id`, and on the remote server). |
| 3 | Prompt Injection Exposure | Yes | 3 | 2 | In one session: it reads issues, pull requests and comments written by anyone on public repositories (untrusted); the token reaches private repositories (private data); and write tools can post comments and open pull requests on public repositories (a way out). This is the pattern in the Invariant Labs GitHub MCP attack (May 2025) cited in `docs/threat-landscape.md`. Default has no isolation. The README's own lockdown mode is "best-effort", "not an authorization boundary", and trusts two bot accounts unconditionally, so it lowers the score to 2 and no further. |
| 4 | Tool Integrity and Supply Chain | Yes | 1 | 1 | Official GitHub repository, tagged release, pinned commit. Docker image signing with cosign is configured in the publish workflow (not verified). One long parameter description (1546 characters on `pull_request_read`) is documentation of its methods, read manually: no hidden instructions found. 37 direct Go dependencies not scanned. |
| 5 | Execution Environment | No | 1 | 1 | Local binary or container, outbound only to the GitHub API (or a configured Enterprise host). Docker gives isolation if used. No shell execution tool found. |
| 6 | Data Exposure | No | 2 | 1 | Private source code, issues and profile data flow to the model provider. Non-default toolsets can read secret-scanning and code-scanning alerts. A single-repository token reduces this to 1. |
| 7 | Output Handling | No | 1 | 1 | Outputs are typed with `additionalProperties: false` in the output schemas I read. Issue and comment bodies are still attacker-written text passed to the model. Inputs are open and unbounded (scanner). |
| 8 | Auditability and Logging | No | 2 | 1 | Command logging exists but is off by default (`--enable-command-logging` writes requests and responses to `--log-file`). GitHub's own audit log records actions as the token's user, so agent actions look like the person's. Hardened: logging on, and a dedicated token or bot account makes agent activity separable. |
| | **Total (0 to 24)** | | **15** | **10** | |

## 4. Verdict

- Hard gate at 3: yes, in the default configuration: Permissions and Scope and Prompt Injection Exposure.
- Total score: 15 default (band: Reject at 15 or more), 10 hardened (band 7 to 14).
- Verdict and reasoning: **Reject in the default configuration**, because it meets the rubric's description of a 3 on two hard gates, and the total also reaches the Reject threshold. The server itself is well engineered, and every control needed to bring it under the line is built in. **Approve with conditions under the hardened profile**, which scores 10. The decision turns on configuration and deployment, not on code quality.

## 5. Conditions

Required to move from Reject to Approve with conditions. Every criterion scored 2 in the hardened column has a control, an owner and a due date.

| Criterion | Compensating control | Owner | Due |
|---|---|---|---|
| 1 Permissions and Scope | Run with `--read-only` unless a task needs writes. If writes are needed, list individual tools with `--tools` (no `delete_*`, `merge_pull_request` or `push_files` by default), and exclude the rest. Client must confirm every write. | Deploying team lead | Before first use |
| 2 Authentication and Token Handling | Fine-grained token limited to named repositories, expiry of 30 days or less, stored outside version control. No classic tokens. | Security reviewer | Before first use |
| 3 Prompt Injection Exposure | Enable `--lockdown-mode`. Limit the token to repositories where all contributors are trusted, or to public repositories only with no private repositories reachable. Treat issue and pull request text as untrusted. | Security reviewer | Before first use |
| 6 Data Exposure | Keep the token's repository list to the minimum and do not enable security-alert toolsets without a separate review. | Platform owner | 30 days |
| 8 Auditability and Logging | Turn on `--enable-command-logging` with a protected `--log-file`. Use a dedicated bot account so GitHub's audit log separates agent activity. | Platform owner | 30 days |

## 6. Residual risk

Even hardened, lockdown is best-effort and a collaborator's account that is compromised, or a trusted bot, can still plant instructions the model will read. The model can still change content in the repositories the token reaches. The system owner accepts this for the named repositories only. No non-gate criterion is scored 3 in either column.

## 7. Re-review triggers

Re-review when the version changes, when a toolset is enabled, when the token's repository list or scopes change, when the remote hosted server is adopted, when another server is added to the same session, or after an advisory for the server or its dependencies. Next scheduled review: 3 months from approval, because this server adds tools often (128 now).

## 8. Calibration note

Did the rubric match my judgement? Yes on the outcome, with three lessons.

1. **Two scanner false positives found by real data and fixed**: free-text `query` parameters were scored like SQL, and `get_commit` was read as a write. Reviews 001 and 002 and the three samples were re-run and are unchanged.
2. **The rubric needs a "configuration profile" idea.** This server scores 15 or 10 depending on how it is run. A single number would have hidden that. The template should record the profile being scored. Suggest adding a "scored profile" row to `reviews/TEMPLATE.md`.
3. **The total threshold and the hard gate agreed here (15, and a gate at 3), but 15 is exactly on the line.** One point lower on any criterion and only the hard gate would have caught it. That supports keeping hard gates separate from the total, and suggests the Reject threshold of 15 is reasonable but untested. After three reviews I have no case that argues for moving it.

Across the three reviews the totals were 13, 11 and 15/10. The riskiest server by capability (GitHub) is also the one with the best built-in controls, and the rubric correctly separates "powerful" from "uncontrolled".
