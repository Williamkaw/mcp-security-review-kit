# MCP manifest scanner

A small Python command line tool that reads the tool list of an MCP server and flags risky patterns. It produces **draft** scores for the rubric criteria it can see evidence for. A human reviewer confirms every score.

The scanner speeds up evidence gathering. It does not replace the review.

## Install and run

```
pip install -r requirements.txt
python mcp_scan.py samples/poisoned.json
python mcp_scan.py samples/poisoned.json --json
python mcp_scan.py path/to/manifest.json --rubric ../rubric/scoring.yaml
```

Input is the JSON returned by an MCP server's `tools/list` call, or any file shaped like `{"tools": [...]}`. An easy way to get one is the MCP Inspector (`npx @modelcontextprotocol/inspector`).

Exit codes: `0` no hard gate tripped, `1` draft reject, `2` bad input. This makes it usable as a CI gate.

## What it reads, and what it scores

The scanner reads `rubric/scoring.yaml` for the criteria. It can draft scores for four of the eight:

| Criterion | What the scanner looks at |
|---|---|
| Permissions and Scope | execution, deletion and write tools, missing confirmation hints, open path and URL parameters, parameters that choose where data is sent, money movement, contact detail changes, wildcard scopes |
| Prompt Injection Exposure | a server that reads outside content and can also send data out (a hint only) |
| Tool Integrity and Supply Chain | hidden instructions and invisible characters in descriptions, read-only claims that contradict the description, duplicate tool names, no pinned version |
| Output Handling | unbounded string parameters, raw query parameters, open input schemas |

The other four criteria (Authentication and Token Handling, Execution Environment, Data Exposure, Auditability and Logging) need evidence that is not in a manifest. They are marked MANUAL and never scored.

A draft score is a **floor**. "At least 0" means the scanner found nothing, which is not the same as safe.

## Samples

| File | What it is | Expected result |
|---|---|---|
| `samples/benign.json` | Narrow, read-only documents server | no findings, NOT DECIDED |
| `samples/poisoned.json` | Deliberately malicious server | draft REJECT, three hard gates |
| `samples/fintech-payments.json` | Realistic payments server, not malicious, sloppy | draft REJECT on Permissions and Scope |

## Limitations

1. **It only sees the manifest.** It cannot see how the server authenticates, where it runs, what data it touches, or what it logs. Those four criteria stay manual.
2. **It can condemn but never approve.** A clean scan proves little. The only verdict it will suggest is reject, and only when a hard gate trips.
3. **It matches English keywords.** Other wording, other languages, encoded text, or instructions split across several fields will slip past. Tool names are classified by simple word lists, so an oddly named tool can be misread.
4. **It does not know your business.** What counts as irreversible, sensitive, or financial is a keyword guess. A human decides what a tool means in the context of your organisation.
5. **Annotations are hints from the server, not guarantees.** The scanner flags a tool that claims `readOnlyHint` while its description says it sends data out, but it cannot verify what the code does.
6. **It cannot see change over time.** There is no baseline or diff, so a tool description that turns hostile after an update (a "rug pull") will not be caught unless you scan every version.
7. **Prompt injection exposure is only a hint.** The critical case needs three things in one session: untrusted input, private data, and a way out. The manifest shows the first and third at best. Whether private data is reachable is a review question.
8. **It is static.** It does not call the server or test live behaviour.

## Calibration notes

The first version scored the payments sample as "at least 2" for Permissions and Scope and never flagged `export_statement`. A human reviewer would score it higher for three reasons:

- `initiate_transfer` moves money, says it cannot be recalled, and declares no confirmation hint.
- `export_statement` claims to be read-only but can deliver a statement to any address through `deliver_to`.
- `update_customer_contact` can change the phone and email on a profile, a common account-takeover step.

Review 1 (filesystem server) exposed a false positive: "file system" in a description matched the execution word list. The pattern no longer matches `system` on its own.

Rules were added for each (`PS-FINANCIAL-ACTION`, `PS-IRREVERSIBLE`, `PS-OUTBOUND-PARAM`, `TI-READONLY-BUT-SENDS`, `PS-IDENTITY-CHANGE`). Multiple hidden-instruction signals on one description are now reported as a single finding, so one root cause is counted once.
