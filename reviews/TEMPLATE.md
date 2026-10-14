# Decision Record: [Server name]

| | |
|---|---|
| Server and publisher | |
| Version or commit hash | |
| Source and date reviewed | |
| Reviewer | |
| Intended use case | |
| Configuration profile scored (default flags, or hardened) | |
| Verdict | **Approve / Approve with conditions / Reject** |

## 1. Scope and evidence

What was reviewed, and what was not. List every source used: README, source code paths, the `tools/list` output, vendor documentation, anything run or tested.

- Reviewed:
- Not reviewed, and why:
- Other servers or tools expected in the same session (a risk can only be judged against what sits beside the server):

## 2. Scanner output

Run `python scanner/mcp_scan.py <manifest.json>` and paste the draft scores and the findings that matter. Count each root cause once. Note any finding you judge to be a false positive and why.

```
(paste output here)
```

## 3. Scores

Score all 8 criteria from `rubric/rubric.md` (0 minimal, 1 low, 2 elevated, 3 critical). Every score needs one line of evidence a second reviewer could check.

| # | Criterion | Hard gate | Score | Evidence |
|---|---|---|---|---|
| 1 | Permissions and Scope | Yes | | |
| 2 | Authentication and Token Handling | Yes | | |
| 3 | Prompt Injection Exposure | Yes | | |
| 4 | Tool Integrity and Supply Chain | Yes | | |
| 5 | Execution Environment | No | | |
| 6 | Data Exposure | No | | |
| 7 | Output Handling | No | | |
| 8 | Auditability and Logging | No | | |
| | **Total (0 to 24)** | | | |

If a criterion cannot be scored from the evidence available, write "Not assessed" and say what evidence is missing. Do not guess.

## 4. Verdict

Apply the decision rules from the rubric.

- Hard gate at 3: yes / no. Which:
- Total score:
- Verdict and reasoning, in two or three sentences:

## 5. Conditions

Required for "Approve with conditions". Every criterion scored 2 needs a compensating control, an owner, and a due date.

| Criterion | Compensating control | Owner | Due |
|---|---|---|---|
| | | | |

## 6. Residual risk

What risk remains after the conditions are met, and who accepts it. A non-gate criterion scored 3 needs a documented risk acceptance from the system owner.

## 7. Re-review triggers

Review again when the server version changes, when a tool is added or its description changes, when the scopes change, or after a security advisory for the server or its dependencies. Next scheduled review:

## 8. Calibration note

Did the rubric give a result that matches your judgment? If not, say where it was too strict or too lenient, and which threshold or level description should change.
