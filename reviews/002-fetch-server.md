# Decision Record 002: Fetch MCP Server

| | |
|---|---|
| Server and publisher | `mcp-server-fetch`, Anthropic, PBC (MCP reference servers), MIT licence, published on PyPI |
| Version or commit hash | 2026.10.10, wheel SHA-256 `d722c48bdc1de3e2a81727853bc490cf55c6c935e2038cdcad3c111b1d85db77` |
| Source and date reviewed | PyPI wheel source (`server.py`, `__init__.py`), 14 October 2026 |
| Reviewer | Bill (draft prepared with Claude, every score to be confirmed by the reviewer) |
| Intended use case | Let a desktop AI assistant read public web pages as markdown, started with default options |
| Verdict | **Approve with conditions** |

## 1. Scope and evidence

- Reviewed: package source (about 520 lines in `server.py`); live `tools/list` output (`reviews/fetch-server/manifest.json`, 1 tool); scanner output; live tests of the private-address block (`reviews/fetch-server/ssrf-tests.py`). Installed from the wheel into an isolated virtual environment (47 packages), wheel hash recorded.
- Not reviewed, and why: the 46 other installed packages (no vulnerability scan); behaviour of fetching real public sites (outbound traffic from my test environment is restricted, so only the refusal paths were tested); DNS rebinding (see criterion 5); Windows behaviour.
- Other servers expected in the same session: none assumed. Section 4 records what changes if the filesystem server (Review 001) is added.

## 2. Scanner output

```
Tools scanned: 1   Findings: 2
  Permissions and Scope [HG]: at least 0
  Prompt Injection Exposure [HG]: at least 1  (hint: server reads external content)
  Tool Integrity and Supply Chain [HG]: at least 0
  Output Handling: at least 1
Draft verdict: NOT DECIDED
```

Both findings are fair. **The scanner missed something a human would flag.** The `fetch` description contains an instruction to the model: "Although originally you did not have internet access, and were advised to refuse and tell the user this, this tool now grants you internet access." From the official publisher this is a harmless capability statement, but it is text that overrides the model's earlier behaviour, which is exactly the shape of tool poisoning. The scanner reported zero Tool Integrity findings. Noted as a known gap, see section 8.

## 3. Scores

| # | Criterion | Hard gate | Score | Evidence |
|---|---|---|---|---|
| 1 | Permissions and Scope | Yes | 1 | One tool, HTTP read only, annotated `readOnlyHint: true`, `destructiveHint: false`. Cannot write, delete or run anything. Reach is any public URL, which is the purpose. |
| 2 | Authentication and Token Handling | Yes | 1 | Local stdio, no authentication, sends no credentials to target sites (User-Agent only). Optional `--proxy-url` may carry proxy credentials set by the operator. |
| 3 | Prompt Injection Exposure | Yes | 2 | Web pages are the most hostile input an agent reads, and the tool is annotated `openWorldHint: true`. A page can tell the model to request an attacker URL with data in the query string, which is a way out. Scored 2 rather than 3 because this server holds no private data on its own. Output is not labelled as untrusted data. |
| 4 | Tool Integrity and Supply Chain | Yes | 1 | Anthropic is the author, version pinned, hash recorded, MIT licence. Held at 1 because the description carries a directive to the model (section 2) and the 46 dependencies were not scanned. |
| 5 | Execution Environment | No | 2 | Runs as the user's process from the user's network. Private, loopback, link-local and cloud-metadata ranges are refused by default, checked on every request including redirects (`_refuse_private_destination`). Live tests refused `127.0.0.1`, `169.254.169.254`, decimal `2130706433`, IPv6-mapped loopback; `file://` failed. Two weaknesses: the check resolves the host and the HTTP client resolves it again to connect, so DNS rebinding was not ruled out; and with a proxy, unresolvable names skip the check. Flags `--allow-private-ips` and `--ignore-robots-txt` remove protections. |
| 6 | Data Exposure | No | 1 | Holds no data of its own and returns public page content. It does reveal the machine's IP address and User-Agent to every site fetched, and the URL itself can carry data out (see criterion 3). |
| 7 | Output Handling | No | 1 | Text only, converted to markdown by default, size bounded (`max_length` up to 999999, default 5000). The `raw` option returns unsanitised HTML. What the client does with it is outside the server. |
| 8 | Auditability and Logging | No | 2 | No logging calls found in the source. Nothing records which URLs were fetched. |
| | **Total (0 to 24)** | | **11** | |

## 4. Verdict

- Hard gate at 3: no.
- Total score: 11 (band 7 to 14).
- Verdict and reasoning: **Approve with conditions**, for the fetch server on its own with default flags. It is read only and its private-network protection is stronger than I expected. The real risk is composition: **fetch combined with the filesystem server from Review 001 meets the rubric's description of a score of 3 for Prompt Injection Exposure** (untrusted content, reachable private data, a way out), which is a hard gate and a Reject. The two are acceptable separately and not acceptable together without isolation or human approval of every fetch.

## 5. Conditions

| Criterion | Compensating control | Owner | Due |
|---|---|---|---|
| 3 Prompt Injection Exposure | Never run in the same session as a tool that can read private data (files, mail, databases) unless every fetch needs human approval. Treat page text as untrusted. | Security reviewer | Before first use |
| 5 Execution Environment | Do not use `--allow-private-ips` or `--ignore-robots-txt`. Run on a network where outbound traffic is filtered, so a DNS rebinding trick cannot reach internal systems. | Platform owner | 30 days |
| 8 Auditability and Logging | Log every fetch URL at the client or through an egress proxy. | Platform owner | 30 days |

## 6. Residual risk

A manipulated model can still make requests to any public site, including ones carrying small amounts of data in the URL. Without private data in the session this is limited to what the model itself knows. The system owner accepts this. No non-gate criterion is scored 3.

## 7. Re-review triggers

Re-review when the version changes, when a tool or description changes, when startup flags change, when any other server is added to the same session, or after an advisory for the package or its dependencies. Next scheduled review: 6 months from approval.

## 8. Calibration note

The total (11) matches my judgement for the server alone. Two findings for the rubric and scanner:

1. **The rubric scores a server, but prompt injection is a property of the session.** Review 001 scored 2 and Review 002 scored 2 for the same criterion, yet together they are a 3. The template now asks which other servers share the session, and a future version of the rubric should require a composition check before approval.
2. **The scanner misses directive text that is not hostile in tone.** The "you now have internet access" sentence did not match any injection pattern. A pattern for sentences that address the model about its own abilities or earlier instructions would catch this one, at the cost of flagging legitimate descriptions for human review. That is the right trade for a tool that only flags.
