# Threat Landscape

Before I build anything, I want to be clear about what can actually go wrong when an LLM is wired to tools through MCP. I read the security guidance in the MCP specification (security best practices and authorization, version 2025-11-25) and the OWASP Top 10 for LLM Applications (2025). Below are the 11 risks I think matter most for this project, in my own words. Some come straight from one source, some sit where the two overlap.

Each risk has three parts: the name, what goes wrong, and an example. Examples marked Real actually happened and link to a source. Examples marked Realistic are scenarios I would expect to see in a fintech or telecom environment.

Last checked against the sources on 14 October 2026. The MCP specification changes, so re-check it before relying on any detail here.

## 1. Prompt Injection (OWASP LLM01)

What goes wrong: The model cannot reliably tell the difference between instructions from me and instructions hidden in the content it reads, so an attacker can steer it by planting text where it will look.

Example (Real): In May 2025, Invariant Labs showed that a malicious issue filed on a public GitHub repository could trick an agent using the GitHub MCP server into reading the owner's private repositories and publishing the contents in a pull request on the public repo. The attacker never touched the agent directly. It needed an agent with access to both public and private repos and tool calls that ran without review, so the weakness is the agent setup as much as the server. [Source](https://invariantlabs.ai/blog/mcp-github-vulnerability)

## 2. Tool Poisoning (MCP, a form of indirect prompt injection, OWASP LLM01)

What goes wrong: A tool's description or parameter text carries hidden instructions. The model reads all of it, but the user usually sees only a short tool name, so the model follows instructions the user never saw.

Example (Real): In April 2025, Invariant Labs demonstrated this against the Cursor coding agent. A harmless-looking tool carried a hidden description that told the agent to read the user's MCP configuration and SSH keys and send them to the attacker's server. The confirmation prompt did not show the full tool input. [Source](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)

## 3. Malicious or Compromised Packages (OWASP LLM03, supply chain)

What goes wrong: An MCP server package is malicious from the start, or turns hostile after an update. Installing it runs someone else's code with my privileges and my trust.

Example (Real): In September 2025, a package called postmark-mcp on npm, posing as the Postmark email integration, added a hidden BCC to its email tool, so a copy of every message went to an outside address. Snyk's timeline has version 1.0.0 published on 15 September 2025 and says the hidden copy began "around 1.0.16", sending mail to an address on the domain giftshop.club. Snyk hedges on the exact version and I did not check the npm history myself, so treat the version number as approximate. [Source](https://snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/)

## 4. Excessive Agency (OWASP LLM06)

What goes wrong: The agent has more tools, permissions, or autonomy than the job needs, so any mistake or manipulation turns into real damage.

Example (Realistic): A support assistant gets a database tool with write access "just in case", and one bad prompt later it edits customer account records instead of reading them.

## 5. Confused Deputy in MCP Proxy Servers (MCP)

What goes wrong: An MCP proxy server talks to a third-party API with one static client ID and lets clients register dynamically. The third-party authorization server sets a consent cookie after the first approval. An attacker registers their own client with their own redirect address and sends the user a crafted link. The browser still holds the cookie, so consent is skipped and the authorization code goes to the attacker, who exchanges it for access to the MCP server as that user.

Example (Realistic): A staff member approves an MCP server once. Weeks later they click a crafted link, consent is skipped, and the attacker ends up with a code they can exchange for access to the staff member's mailbox or file store through the proxy.

Source: [MCP security best practices, confused deputy problem](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)

## 6. Token Passthrough (MCP)

What goes wrong: The MCP server accepts any token a client hands it, without checking it was issued to that server, and passes it on to the downstream API. That lets callers dodge controls that depend on the token's audience and wrecks the audit trail. The specification forbids it.

Example (Realistic): A stolen token that was never issued for the MCP server is accepted anyway and forwarded to the finance API. The finance logs show the token owner as the caller, with no sign of the server that relayed it, and the MCP server cannot tell its own clients apart, so incident response starts blind.

Source: [MCP security best practices, token passthrough](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)

## 7. Server-Side Request Forgery During OAuth Discovery (MCP)

What goes wrong: During OAuth discovery the client fetches several URLs that a malicious MCP server controls. The server can fill them with internal addresses, and the client follows them from inside the network.

Example (Realistic): A cloud-hosted MCP client is pointed at the cloud provider's link-local metadata address. It fetches the instance's credentials, and details can leak back to the attacker through error messages or the OAuth flow.

Source: [MCP security best practices, SSRF](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)

## 8. Local MCP Server Compromise (MCP)

What goes wrong: Local MCP servers run with my privileges, so a malicious startup command or a poisoned server package gets arbitrary code execution on my machine, often with no visibility into what ran. A server left running on localhost can also be reached by other processes.

Example (Realistic): I paste a one-click install config from a blog post. The start command quietly reads my SSH keys and posts them to an external host before launching the real server.

Source: [MCP security best practices, local server compromise](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)

## 9. Malicious Authorization URLs (MCP)

What goes wrong: A hostile server returns a crafted authorization URL, and a client that opens it carelessly (through a shell, or with a javascript: scheme) ends up running attacker code.

Example (Real): CVE-2025-6514 in mcp-remote (versions 0.0.5 to 0.1.15). A malicious server could return a crafted authorization endpoint that the client passed to a function that opened it, which led to command injection. It was rated 9.6 (critical), reported by the JFrog security research team, and fixed in 0.1.16. [Source](https://www.wiz.io/vulnerability-database/cve/cve-2025-6514)

## 10. Sensitive Information Disclosure (OWASP LLM02)

What goes wrong: The model or its tools leak data they should not, such as secrets in context, other users' records, or credentials returned in tool output and logs.

Example (Realistic): A shared assistant with access to a client folder summarizes one customer's contract in a chat with another customer, because nothing separated their data.

## 11. Improper Output Handling (OWASP LLM05)

What goes wrong: Model output gets treated as trusted and passed straight into a browser, shell, or database without validation, so a manipulated model becomes a way to attack the systems behind it.

Example (Realistic): An agent writes a "report" containing a script tag, and the dashboard renders it unescaped. Anyone who opens the page runs the attacker's code.

## Families

I group the risks into six families. The rubric criteria are built on these.

| Family | Risks | Main rubric criteria |
|---|---|---|
| Instruction integrity | 1 Prompt Injection, 2 Tool Poisoning | Prompt Injection Exposure, Tool Integrity and Supply Chain |
| Permissions and agency | 4 Excessive Agency | Permissions and Scope |
| Identity and authorization | 5 Confused Deputy, 6 Token Passthrough | Authentication and Token Handling |
| Supply chain and execution | 3 Malicious Packages, 7 SSRF, 8 Local Server Compromise, 9 Malicious Authorization URLs | Tool Integrity and Supply Chain, Execution Environment |
| Data exposure | 10 Sensitive Information Disclosure | Data Exposure |
| Output handling | 11 Improper Output Handling | Output Handling |

Auditability and Logging cuts across all of them. Risk 6 is the clearest case: without logs that identify the real caller, none of the others can be investigated properly.

## What I left out, and why

OWASP also covers data and model poisoning, system prompt leakage, vector and embedding weaknesses, misinformation, and unbounded consumption. They are real, but they are about model training, retrieval, or cost. I wanted this list to stay focused on the tool and protocol layer.

From the MCP specification I have not made separate entries for session hijacking (a prompt injection variant through a shared event queue, and an impersonation variant using a stolen session ID) or the stdio proxy escalation path. The scope minimization guidance feeds into risk 4, and session hijacking overlaps with the identity risks (5 and 6). I may split them out later.

## Sources

- [MCP specification, security best practices (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/security_best_practices)
- [MCP specification, authorization (2025-11-25)](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization)
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/llm-top-10/)
- [Invariant Labs, tool poisoning attacks (April 2025)](https://invariantlabs.ai/blog/mcp-security-notification-tool-poisoning-attacks)
- [Invariant Labs, GitHub MCP vulnerability (May 2025)](https://invariantlabs.ai/blog/mcp-github-vulnerability)
- [Snyk, malicious postmark-mcp package (September 2025)](https://snyk.io/blog/malicious-mcp-server-on-npm-postmark-mcp-harvests-emails/)
- [Wiz vulnerability database, CVE-2025-6514](https://www.wiz.io/vulnerability-database/cve/cve-2025-6514)
