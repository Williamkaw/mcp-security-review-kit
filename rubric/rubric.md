# MCP Security Review Rubric

Scoring: each criterion is scored by risk level.
0 = minimal risk, 1 = low, 2 = elevated, 3 = critical.
A score of 3 on a hard-gate criterion (marked HG) means automatic reject.

## 1. Permissions and Scope (HG)

**What it tests:** whether the server can do more than its use case needs. This sets the blast radius when the model is manipulated.

**Evidence to collect:** full tool list, requested OAuth scopes, filesystem and network access, which tools write, delete or execute, and whether state-changing tools require confirmation.

| Score | Description |
|---|---|
| 0 | Read-only tools, limited to the specific resources the use case needs. No write, delete or execute capability. Scopes are documented and minimal. |
| 1 | A few write actions on a narrow, named set of resources. Every state-changing tool needs human confirmation. Scopes match the documented use case. |
| 2 | Broad read access across a system, or write access beyond the use case. Confirmation is inconsistent. Scopes are wider than needed but limited to one system. |
| 3 | Wildcard or admin scopes, shell or code execution, arbitrary file or network access, or destructive actions with no confirmation. Scope cannot be narrowed. |

**Maps to:** OWASP LLM06 (Excessive Agency), LLM01 (blast radius of prompt injection). NIST AI RMF: MAP and MANAGE functions. ISO/IEC 27001:2022 Annex A 5.15 (access control) and 8.2 (privileged access rights). ISO/IEC 42001:2023 Annex A.9 (use of AI systems), A.9.4 (intended use).

## 2. Authentication and Token Handling (HG)

**What it tests:** whether the server proves who is calling, and whether tokens stay inside the boundary they were issued for.

**Evidence to collect:** auth method, token audience validation, token lifetime, where secrets are stored, whether any token is forwarded downstream, and for proxy servers, how user consent is tracked per client.

| Score | Description |
|---|---|
| 0 | Every request authenticated (OAuth 2.1 with PKCE or equivalent). Tokens are validated for audience, short-lived, and never forwarded. Secrets are in a vault. Consent is recorded per client. |
| 1 | Authenticated, and audience is validated. Minor gaps: longer token lifetime, manual rotation, secrets held in environment variables. |
| 2 | Authentication is weak: a static shared API key, no audience validation, tokens in config files or logs, or consent not tracked per client. |
| 3 | No authentication on a network-reachable server. Or token passthrough. Or credentials appearing in tool output or logs. Or a static client ID proxy that skips consent. |

**Maps to:** OWASP LLM02 (Sensitive Information Disclosure), LLM03 (Supply Chain). MCP spec risks: token passthrough, confused deputy, malicious authorization URLs. NIST AI RMF: MANAGE and GOVERN functions. ISO/IEC 27001:2022 Annex A 5.17 (authentication information) and 8.5 (secure authentication). ISO/IEC 42001:2023 Annex A.10 (third-party and customer relationships).
## 3. Prompt Injection Exposure (HG)

**What it tests:** whether attacker-controlled text can reach the model while it holds sensitive access and the ability to act.

**Evidence to collect:** what external content the server ingests (email, issues, web pages, documents, user uploads), what private data is reachable in the same session, and whether any tool can send data out.

| Score | Description |
|---|---|
| 0 | Ingests no untrusted content. All inputs come from trusted, authenticated internal sources. |
| 1 | Ingests untrusted content, but the session has read-only tools and no route to send data out. Content is labelled as data. |
| 2 | Ingests untrusted content in a session that also has write tools. Mitigations are partial or undocumented. |
| 3 | In one session: ingests untrusted content, can reach private data, and can communicate externally. No isolation or confirmation. |

**Maps to:** OWASP LLM01. NIST AI RMF: MAP, MEASURE. ISO/IEC 27001:2022 Annex A 8.26 (application security requirements), 8.12 (data leakage prevention).

## 4. Tool Integrity and Supply Chain (HG)

**What it tests:** whether you can trust the code and the tool descriptions, now and after the next update.

**Evidence to collect:** publisher identity, source availability, version pinning, signed releases or hashes, a manual read of every tool description, and whether changes to tools are detected.

| Score | Description |
|---|---|
| 0 | Verified publisher, source reviewed, version and hash pinned, tool descriptions reviewed, changes alert a human. |
| 1 | Reputable publisher with source available and a pinned version. No formal review of descriptions. |
| 2 | Unpinned versions, a single anonymous maintainer, or no change detection. |
| 3 | Unverifiable source, obfuscated code, hidden instructions in tool descriptions, or auto-update from an unpinned source. |

**Maps to:** OWASP LLM03. NIST AI RMF: GOVERN, MANAGE. ISO/IEC 27001:2022 Annex A 5.19 to 5.21 (supplier and ICT supply chain), 8.28 (secure coding). ISO/IEC 42001:2023 Annex A.10.3 (suppliers).

## 5. Execution Environment

**What it tests:** what the server can reach on the machine and the network if it is compromised.

**Evidence to collect:** where it runs (local or hosted), privilege level, sandboxing, startup command, network egress rules, and whether it follows URLs supplied by remote parties.

| Score | Description |
|---|---|
| 0 | Sandboxed container, no host access, egress allowlist, fixed startup command. |
| 1 | Sandboxed, with somewhat broad egress. |
| 2 | Runs with the user's privileges, or has open egress. |
| 3 | Admin privileges, startup command taken from remote config, or can reach internal networks or cloud metadata, or follows server-supplied URLs without validation. |

**Maps to:** MCP spec risks: local server compromise, SSRF, malicious authorization URLs. ISO/IEC 27001:2022 Annex A 8.20 (network security), 8.22 (segregation), 8.9 (configuration management).

## 6. Data Exposure

**What it tests:** what data the server touches, who can see it, and where it goes.

**Evidence to collect:** data classes accessed, per-user isolation, whether secrets can appear in output or logs, retention, and every third-party destination.

| Score | Description |
|---|---|
| 0 | Public or non-sensitive data only. |
| 1 | Internal data, strict per-user isolation, nothing leaves the organisation. |
| 2 | Confidential data, shared context across users, or data sent to a third party without an agreement. |
| 3 | Regulated or secret data without isolation, credentials in output, or unknown data destinations. |

**Maps to:** OWASP LLM02. ISO/IEC 27001:2022 Annex A 5.12 (classification), 5.34 (privacy and PII), 8.12 (data leakage prevention). Also check applicable data protection law, such as Ghana's Data Protection Act, 2012 (Act 843), when personal data is involved.

## 7. Output Handling

**What it tests:** whether model and tool output is treated as untrusted before it reaches a browser, shell, or database.

**Evidence to collect:** where outputs are rendered or passed, schema validation, escaping, and whether any output is ever executed.

| Score | Description |
|---|---|
| 0 | Structured outputs validated against a schema, escaped for their destination, never executed. |
| 1 | Mostly validated, with minor gaps in low-risk paths. |
| 2 | Free text passed to downstream systems or rendered with only partial validation. |
| 3 | Output is executed, or rendered unescaped, or concatenated into queries. |

**Maps to:** OWASP LLM05. ISO/IEC 27001:2022 Annex A 8.28 (secure coding), 8.26.

## 8. Auditability and Logging

**What it tests:** whether you can reconstruct who did what, and tell a human action from a model action.

**Evidence to collect:** what is logged, whether user identity is captured, parameters and results, tamper protection, retention, and whether logs reach your SIEM.

| Score | Description |
|---|---|
| 0 | Every call logged with user identity, parameters, timestamp, and result. Tamper-evident, sent to the SIEM, retention meets policy. |
| 1 | Logged with identity, with minor gaps in retention or export. |
| 2 | Partial logs, or no way to attribute an action to a user. |
| 3 | No logs, or logs that contain secrets. |

**Maps to:** ISO/IEC 27001:2022 Annex A 8.15 (logging), 8.16 (monitoring). NIST AI RMF: MEASURE, MANAGE. ISO/IEC 42001:2023 Annex A.6.2.8 (AI system recording of event logs).

## Decision rules

Total score = sum of all 8 criteria (0 to 24). Hard gates are criteria 1 to 4.

| Verdict | Rule |
|---|---|
| Reject | Any hard gate scores 3, or total is 15 or more. |
| Approve with conditions | Total 7 to 14, no hard gate at 3. Every criterion scored 2 needs a named compensating control, an owner, and a due date. |
| Approve | Total 0 to 6, and no criterion above 1. |

Any non-gate criterion at 3 needs a documented risk acceptance from the system owner before approval. The thresholds are a starting point and will be calibrated after the worked reviews.

ISO/IEC 42001 control numbers were checked against a published summary of the 2023 edition (Annex A groups A.2 to A.10). Confirm them against your licensed copy of the standard before citing them in an audit.
