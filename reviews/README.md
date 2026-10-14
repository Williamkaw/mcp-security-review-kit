# Reviews

Each review is a decision record built from [`TEMPLATE.md`](TEMPLATE.md). The evidence behind it sits in a folder of the same topic: the captured tool list (`manifest.json`) and any scripts used to test the server.

| # | Server | Total | Verdict | Evidence folder |
|---|---|---|---|---|
| [001](001-filesystem-server.md) | Filesystem server 1.0.0 | 13 | Approve with conditions | [`filesystem-server/`](filesystem-server) |
| [002](002-fetch-server.md) | Fetch server 2026.10.10 | 11 | Approve with conditions | [`fetch-server/`](fetch-server) |
| [003](003-github-server.md) | GitHub server v2.0.2 | 15 default, 10 hardened | Reject by default; approve with conditions when hardened | [`github-server/`](github-server) |

To repeat a scan: `python scanner/mcp_scan.py reviews/<folder>/manifest.json`.

Scores are drafts for a human reviewer to confirm. They are a worked example of the method, not an endorsement or a condemnation of any product.
