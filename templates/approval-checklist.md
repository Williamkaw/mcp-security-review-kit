# MCP Server Approval Checklist

Used by the reviewer from intake to sign-off. Tick a box only when the evidence is attached or linked in the decision record (`reviews/TEMPLATE.md`).

| | |
|---|---|
| Server and version | |
| Decision record | |
| Reviewer | |
| Date | |

## A. Before scoring

- [ ] Intake form complete and signed by the requester and the system owner.
- [ ] Exact version, commit or package hash recorded. Install source verified against the registry.
- [ ] Package installed in an isolated place with install scripts disabled.
- [ ] Real `tools/list` output captured (or the reason it could not be captured is written down).
- [ ] Scanner run on the manifest. Every finding counted by root cause. False positives explained.
- [ ] Every tool description read by a person for instructions aimed at the model.
- [ ] Other servers in the same session listed, and the combination considered.

## B. Evidence per criterion

| # | Criterion | Evidence needed | Done |
|---|---|---|---|
| 1 | Permissions and Scope | Tool list with read, write, delete and execute marked; scopes; confirmation behaviour | [ ] |
| 2 | Authentication and Token Handling | Auth method; token audience, lifetime and storage; any forwarding | [ ] |
| 3 | Prompt Injection Exposure | Untrusted inputs; private data reachable; outbound routes | [ ] |
| 4 | Tool Integrity and Supply Chain | Publisher; pinned version; hash or signature; dependency check | [ ] |
| 5 | Execution Environment | Where it runs; privilege; sandbox; network egress | [ ] |
| 6 | Data Exposure | Data classes reachable; filtering; legal basis for personal data | [ ] |
| 7 | Output Handling | What the output is passed to; schema limits; escaping | [ ] |
| 8 | Auditability and Logging | What is logged, where, who can read it, retention | [ ] |

A criterion that cannot be assessed is marked "Not assessed" with the missing evidence named. It is not guessed.

## C. Decision rules applied

- [ ] Any hard gate (criteria 1 to 4) at 3: **Reject**.
- [ ] Total 15 or more: **Reject**.
- [ ] Total 7 to 14 with no hard gate at 3: **Approve with conditions**. Each criterion scored 2 has a control, an owner and a due date.
- [ ] Total 0 to 6 and no criterion above 1: **Approve**.
- [ ] Any non-gate criterion at 3 has a written risk acceptance from the system owner.
- [ ] Configuration profile that was scored is stated.

## D. Sign-off

| Role | Name | Decision | Date |
|---|---|---|---|
| Reviewer | | | |
| System owner (accepts residual risk) | | | |
| Security lead or CISO | | | |

## E. After approval

- [ ] Conditions tracked to their due dates.
- [ ] Re-review triggers set: version change, tool or description change, scope change, new server in the session, security advisory.
- [ ] Next scheduled review date entered in the risk register.
