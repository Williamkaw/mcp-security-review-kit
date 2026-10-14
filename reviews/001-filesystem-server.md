# Decision Record 001: Filesystem MCP Server

| | |
|---|---|
| Server and publisher | `@modelcontextprotocol/server-filesystem`, MCP reference servers (modelcontextprotocol/servers) |
| Version or commit hash | npm 1.0.0, integrity `sha512-2fN6qhpsiPSBAe0ev1qDPk4sCWdULCZQTuYc4ZY7+BDWQ1XCxLB+7dqStF2ZflgG4G/9vTwQsjxh7pjFqrrpcg==` |
| Source and date reviewed | npm package source and vendor README, 14 October 2026 |
| Reviewer | Bill |
| Intended use case | Local stdio server giving a desktop AI assistant read and write access to one project folder |
| Verdict | **Approve with conditions** |

## 1. Scope and evidence

- Reviewed: vendor README; the published package source (`dist/server.js`, `lib.js`, `path-validation.js`, `path-utils.js`, `roots-utils.js`); the live `tools/list` output (`reviews/filesystem-server/manifest.json`, 14 tools); scanner output; a live test of path handling (`reviews/filesystem-server/path-tests.py`). The package was installed in an isolated folder with install scripts disabled and the lockfile integrity checked against `npm view`.
- Not reviewed, and why: the 104 transitive dependencies (no software composition scan run); npm provenance attestation (not checked); behaviour on Windows and in Docker (tested on Linux only); race conditions between validation and use (the code has notes on this, I did not test it); MCP client behaviour (confirmation prompts belong to the client).

## 2. Scanner output

First run: draft REJECT on Permissions and Scope (at least 3). That was a **false positive**: the word "system" in "from the file system" matched the execution word list, so `read_text_file` was labelled a command-execution tool, which also caused a bogus annotation-mismatch finding. The scanner was fixed (`EXEC_WORDS`), the three samples were re-run with unchanged results, and the server was re-scanned.

Second run, after the fix:

```
Tools scanned: 14   Findings: 32
  Permissions and Scope [HG]: at least 2  (15 findings)
  Tool Integrity and Supply Chain [HG]: at least 0  (0 findings)
  Prompt Injection Exposure [HG]: at least 0  (0 findings)
  Output Handling: at least 1  (17 findings)
Draft verdict: NOT DECIDED
```

Findings that matter: 11 `PS-OPEN-PATH` (every tool takes a free `path`) and 4 `PS-WRITE`. Judgement: `PS-OPEN-PATH` is true but is the purpose of a filesystem server. It is only acceptable because the server enforces an allowed-directory list, which the scanner cannot see (see criterion 1). The 17 Output Handling findings are the same two root causes repeated: no `additionalProperties: false`, and unbounded strings.

## 3. Scores

| # | Criterion | Hard gate | Score | Evidence |
|---|---|---|---|---|
| 1 | Permissions and Scope | Yes | 2 | Four write tools; `write_file`, `edit_file`, `move_file` declare `destructiveHint: true`, so clients can ask for confirmation. Every path is checked against an allowed-directory list and symlinks are resolved with `realpath` (`lib.js`). Live test: a symlink to `/etc/hostname`, a `..` escape and `/etc/passwd` were all denied. Score stays at 2 because the blast radius is whatever directory is configured, and write access is on by default. |
| 2 | Authentication and Token Handling | Yes | 1 | Local stdio, no authentication, no tokens, no network listener in the code reviewed. Trust rests on the parent process. Not scored 0 because there is no identity check at all. Does not apply as written to a remote deployment. |
| 3 | Prompt Injection Exposure | Yes | 2 | Read tools return raw file content to the model, so any instruction inside a file is read as context. The server has no outbound network tool (`openWorldHint: false`), so it cannot exfiltrate alone. The risk appears when combined with a network or GitHub tool in the same session. Content sanitising was not tested. |
| 4 | Tool Integrity and Supply Chain | Yes | 1 | Official reference repository, six npm maintainers, exact version pinned, lockfile integrity matches the registry, no hidden text or invisible characters in descriptions (0 scanner findings). Held at 1 because 104 transitive dependencies and provenance were not assessed. |
| 5 | Execution Environment | No | 2 | Runs as the user's own process with that user's full file rights; the allowed-directory list is application-level only, not an OS sandbox. README documents Docker bind mounts with a read-only option, which would lower this. |
| 6 | Data Exposure | No | 2 | Can read anything inside the allowed directories, including `.env` files and keys if present. No secret filtering. `excludePatterns` exists on search and tree tools only. |
| 7 | Output Handling | No | 1 | Returns text, diffs and JSON; no code execution or rendering. Input schemas are open and unbounded (scanner), but the path and null-byte checks in `path-validation.js` limit practical harm. |
| 8 | Auditability and Logging | No | 2 | The only logging found is `console.error` for roots updates. No record of which file was read or written. Logging has to come from the client or a wrapper. |
| | **Total (0 to 24)** | | **13** | |

## 4. Verdict

- Hard gate at 3: no.
- Total score: 13 (band 7 to 14).
- Verdict and reasoning: **Approve with conditions.** The server enforces its boundaries well (symlink and traversal tests passed), has no network reach and no authentication surface. Its risk comes from configuration: how broad the allowed directory is, whether writes are needed, and what other tools sit beside it.

## 5. Conditions

| Criterion | Compensating control | Owner | Due |
|---|---|---|---|
| 1 Permissions and Scope | Allow one project folder only, never a home directory or drive root. Require client confirmation for all write tools. Use a read-only mount where writes are not needed. | Deploying team lead | Before first use |
| 3 Prompt Injection Exposure | Do not run this server in the same session as any tool that can send data out (fetch, email, GitHub write) unless a human approves each outbound call. | Security reviewer | Before first use |
| 5 Execution Environment | Run in a container or restricted OS account for anything beyond personal use. | Platform owner | 30 days |
| 6 Data Exposure | Keep secrets, `.env` files and keys out of the allowed folder, and add a secret scan of that folder. | Deploying team lead | Before first use |
| 8 Auditability and Logging | Log tool calls at the client or with a wrapper (tool, path, time, user). | Platform owner | 30 days |

## 6. Residual risk

A manipulated model can still read every file in the allowed folder and overwrite files in it, and the server cannot tell a legitimate request from a manipulated one. The system owner accepts this risk for the chosen folder. No non-gate criterion is scored 3, so no formal risk acceptance is triggered.

## 7. Re-review triggers

Re-review when the version changes, when a tool is added or its description changes, when the allowed directories change, when it is deployed remotely, or after an advisory for the server or its dependencies. Next scheduled review: 6 months from approval.

## 8. Calibration note

The rubric gave a result that matches my judgement (13, approve with conditions). Two lessons. First, the scanner produced a false REJECT from one common phrase, so keyword lists need a check against real servers, not only crafted samples. Second, `PS-OPEN-PATH` fires on every filesystem tool by design; for servers whose purpose is file access the scanner cannot distinguish "unbounded" from "bounded by a server-side allow-list". Consider lowering it for path parameters when the description says access is limited to allowed directories, but only after reviews 2 and 3 show whether that generalises.
