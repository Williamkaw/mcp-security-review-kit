# MCP Server Intake Form

Completed by the team that wants to use the server, before any review starts. A reviewer cannot score a server without knowing how it will be used, so an incomplete form is returned, not reviewed.

| | |
|---|---|
| Request date | |
| Requested by (name, team) | |
| System owner (accepts the residual risk) | |
| Server name and publisher | |
| Source link (repository or package page) | |
| Version or commit to approve | |

## 1. Purpose

- What job will this server do, in one or two sentences?
- Why is a connector needed, and what happens today without it?
- Who will use it, and how many people?

## 2. How it will run

| Question | Answer |
|---|---|
| Local on a laptop, on a shared server, or hosted by the publisher? | |
| Which AI client or host will connect to it? | |
| Which AI model or provider receives the server's output? | |
| Is it started by a command (npx, uvx, docker)? Paste the exact command. | |
| Configuration profile requested (default flags, read-only, other) | |

## 3. Access it needs

| Question | Answer |
|---|---|
| Which systems, folders, repositories or accounts will it touch? | |
| Read only, or does it need to write, send, delete or run anything? | |
| How does it authenticate (none, API key, personal token, OAuth, service account)? | |
| Who issues the credential, what are its scopes, and when does it expire? | |
| Does any tool let the caller choose a path, URL, address or recipient? | |

## 4. Data it will see

| Question | Answer |
|---|---|
| Highest data class reachable (public, internal, confidential, personal, financial)? | |
| Is personal data involved? If yes, which law applies (for example Ghana Data Protection Act, 2012, Act 843, or GDPR)? | |
| Can data leave the organisation through this server, or through the model provider? | |
| Does the server read content written by outsiders (web pages, issues, email, uploads)? | |

## 5. Other tools in the same session

List every other server or tool the assistant will have at the same time. Risk comes from combinations: untrusted input, private data and a way out in one session.

| Other server or tool | Reads private data? | Reads outside content? | Can send data out? |
|---|---|---|---|
| | | | |

## 6. Declarations

- [ ] I have read the vendor documentation and listed every tool I need.
- [ ] I have asked for the least access that does the job.
- [ ] I understand the server may be re-reviewed when it changes.

Signed (requester): __________________ Date: ____________
