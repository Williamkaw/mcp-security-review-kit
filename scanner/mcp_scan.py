#!/usr/bin/env python3
"""mcp_scan: static scanner for MCP tool manifests.

Reads the JSON returned by an MCP server's `tools/list` call (or a file shaped
like {"tools": [...]}) and flags risky patterns. It produces DRAFT scores for
the rubric criteria it can actually see evidence for. A human reviewer confirms
every score. Criteria that need evidence outside the manifest (authentication,
execution environment, data exposure, logging) are marked MANUAL, never scored.

Usage:
    python mcp_scan.py manifest.json
    python mcp_scan.py manifest.json --json
    python mcp_scan.py manifest.json --rubric ../rubric/scoring.yaml
"""
import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path

import yaml

# ---------------------------------------------------------------- rules

# Hidden-instruction patterns in tool descriptions (tool poisoning).
INJECTION_PATTERNS = [
    (r"ignore (all |any )?(previous|prior|above) (instructions|rules)", "override of prior instructions"),
    (r"do not (tell|inform|mention|reveal|show)[^.]{0,40}(user|human)", "instruction to hide behaviour from the user"),
    (r"don'?t (tell|inform|mention|reveal)[^.]{0,40}(user|human)", "instruction to hide behaviour from the user"),
    (r"<\s*(important|system|instructions?)\s*>", "pseudo-system tag in description"),
    (r"before (using|calling|running) this tool[^.]{0,80}(read|send|include|pass)", "pre-call side action demanded"),
    (r"(~|/home/\w+|%userprofile%)?[/\\]?\.ssh\b|id_rsa|\.aws[/\\]credentials|\.env\b", "references secret or credential files"),
    (r"\b(send|post|forward|upload|exfiltrate)\b[^.]{0,60}\b(to|at)\b[^.]{0,40}(http|https|@|\.com|\.io)", "instruction to send data to an external destination"),
    (r"\bbcc\b", "mentions BCC (possible silent copy of data)"),
    (r"<!--.*?-->", "HTML comment hidden in description"),
]

# Names or descriptions that signal dangerous capability.
EXEC_WORDS = r"\b(exec|execute|shell|bash|powershell|cmd|eval|run[_ ]?(command|script|code)|subprocess|(?<!file )(?<!operating )system call|os\.system)\b"
DELETE_WORDS = r"\b(delete|remove|drop|truncate|destroy|purge|wipe|erase|kill)\b"
WRITE_WORDS = r"\b(write|create|update|modify|edit|insert|send|post|put|patch|upload|move|rename|set|deploy|commit|push|transfer|pay)\b"
SQL_WORDS = r"\b(sql|query)\b"

# Parameter names that suggest paths or URLs.
PATH_PARAMS = {"path", "file", "filepath", "file_path", "filename", "dir", "directory", "folder"}
URL_PARAMS = {"url", "uri", "endpoint", "webhook", "href", "link", "host"}

# Zero-width code points, written as numbers so this source file has no hidden characters.
ZERO_WIDTH = {0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF}

# Parameters that let the caller choose where data goes.
OUTBOUND_PARAM = r"(deliver_?to|send_?to|recipients?|to_?(address|email)|cc|bcc|notify(_\w+)?|webhook(_\w+)?|callback(_\w+)?|reply_?to|forward_?to)"
# Descriptions that say data is sent or delivered somewhere.
EGRESS_DESC = r"\b(deliver(s|ed)?|sends?|emails?|forwards?|uploads?|posts?|publish(es)?)\b[^.]{0,60}\b(to|at)\b"
# Money movement and irreversibility signals.
FINANCIAL_WORDS = r"\b(transfer|payment|payout|withdraw\w*|disburse\w*|wire|remit\w*|refund|settle\w*|debit)\b"
IRREVERSIBLE_DESC = r"\b(cannot|can't|can not) be (undone|recalled|reversed|rolled back|recovered)\b|\birreversible\b|\bpermanent(ly)?\b"
# Fields where a change is a common account-takeover step.
IDENTITY_FIELDS = r"\b(phone|msisdn|email|password|passcode|mfa|otp|beneficiary)\b"

WILDCARD_SCOPES = {"*", "all", "admin", "root", "full_access", "full-access", "owner", "superuser"}
BROAD_SCOPE_PATTERN = re.compile(r"(^|[:._-])(admin|write_all|full|\*|all)([:._-]|$)", re.I)

# Rubric criteria this scanner can draft a score for. Everything else is MANUAL.
SCANNABLE = ["permissions_scope", "prompt_injection_exposure", "tool_integrity_supply_chain", "output_handling"]


@dataclass
class Finding:
    criterion: str      # rubric criterion id
    floor: int          # minimum draft score this finding supports (1 to 3)
    tool: str           # tool name or "<server>"
    rule: str           # short rule id
    detail: str         # human-readable explanation


# ---------------------------------------------------------------- helpers

def invisible_chars(text: str):
    """Return invisible or direction-control characters found in text."""
    bad = []
    for ch in text:
        cat = unicodedata.category(ch)
        if cat in ("Cf", "Co") or ord(ch) in ZERO_WIDTH:
            bad.append(f"U+{ord(ch):04X}")
    return sorted(set(bad))


def schema_props(tool: dict) -> dict:
    schema = tool.get("inputSchema") or tool.get("input_schema") or {}
    return schema.get("properties") or {}


def classify_tool(tool: dict) -> str:
    """Rough capability class: exec, delete, write, read."""
    name = str(tool.get("name", "")).lower().replace("-", "_")
    desc = str(tool.get("description", "")).lower()
    text = f"{name.replace('_', ' ')} {desc}"
    if re.search(EXEC_WORDS, text):
        return "exec"
    if re.search(DELETE_WORDS, name.replace("_", " ")) or re.search(DELETE_WORDS, desc[:120]):
        return "delete"
    if re.match(r"(get|list|search|read|find|describe)_", name):
        return "read"  # a read verb at the start of the name wins over words like "commit"
    if re.search(WRITE_WORDS, name.replace("_", " ")):
        return "write"
    return "read"


# ---------------------------------------------------------------- checks

def check_descriptions(tool, name, findings):
    texts = [("description", str(tool.get("description", "")))]
    for pname, pdef in schema_props(tool).items():
        if isinstance(pdef, dict) and pdef.get("description"):
            texts.append((f"param '{pname}'", str(pdef["description"])))

    for where, text in texts:
        labels = []
        for pattern, label in INJECTION_PATTERNS:
            if re.search(pattern, text, re.I | re.S) and label not in labels:
                labels.append(label)
        if labels:
            findings.append(Finding(
                "tool_integrity_supply_chain", 3, name, "TI-HIDDEN-INSTRUCTION",
                f"{where}: {len(labels)} signal(s): " + "; ".join(labels)
                + ". Treat as tool poisoning until a human clears it."))
        inv = invisible_chars(text)
        if inv:
            findings.append(Finding(
                "tool_integrity_supply_chain", 3, name, "TI-INVISIBLE-CHARS",
                f"{where} contains invisible characters ({', '.join(inv)}). These can hide instructions from reviewers."))
        if len(text) > 1200:
            findings.append(Finding(
                "tool_integrity_supply_chain", 2, name, "TI-LONG-DESCRIPTION",
                f"{where} is {len(text)} characters. Unusually long descriptions deserve a manual read."))
        if re.search(r"[A-Za-z0-9+/]{80,}={0,2}", text):
            findings.append(Finding(
                "tool_integrity_supply_chain", 2, name, "TI-ENCODED-BLOB",
                f"{where} contains a long encoded-looking string."))


def check_capability(tool, name, findings):
    cls = classify_tool(tool)
    ann = tool.get("annotations") or {}
    read_only = ann.get("readOnlyHint")
    destructive = ann.get("destructiveHint")
    props = schema_props(tool)

    if cls == "exec":
        findings.append(Finding("permissions_scope", 3, name, "PS-EXECUTION",
                                "Tool appears to execute commands or code. Needs sandbox and human confirmation."))
    elif cls == "delete":
        floor = 3 if destructive is not False and read_only is not True and not ann else 2
        findings.append(Finding("permissions_scope", floor, name, "PS-DESTRUCTIVE",
                                "Tool appears to delete or destroy data."
                                + ("" if ann else " No annotations declare destructive behaviour.")))
    elif cls == "write":
        findings.append(Finding("permissions_scope", 1, name, "PS-WRITE",
                                "Tool can change state. Confirm each write needs human approval."))

    if cls in ("write", "delete", "exec") and read_only is None and destructive is None:
        findings.append(Finding("permissions_scope", 2, name, "PS-NO-ANNOTATIONS",
                                "State-changing tool declares no readOnlyHint or destructiveHint, so a client cannot know to ask for confirmation."))
    if read_only is True and cls in ("write", "delete", "exec"):
        findings.append(Finding("tool_integrity_supply_chain", 2, name, "TI-ANNOTATION-MISMATCH",
                                "Tool claims readOnlyHint=true but its name or description suggests it changes state."))

    desc_text = str(tool.get("description", ""))
    name_desc = f"{name} {desc_text}".lower().replace("_", " ")

    if read_only is True and re.search(EGRESS_DESC, desc_text, re.I):
        findings.append(Finding("tool_integrity_supply_chain", 2, name, "TI-READONLY-BUT-SENDS",
                                "Tool claims readOnlyHint=true but its description says it sends or delivers data to a destination."))

    for pname in props:
        pl = pname.lower()
        if re.fullmatch(OUTBOUND_PARAM, pl) or (pl == "to" and re.search(r"\b(send|email|mail|message)\b", name_desc)):
            findings.append(Finding("permissions_scope", 2, name, "PS-OUTBOUND-PARAM",
                                    f"Parameter '{pname}' lets the caller choose where data is sent. A manipulated model could route data to an attacker."))

    if cls in ("write", "delete", "exec") and re.search(FINANCIAL_WORDS, name_desc):
        confirmable = destructive is True
        findings.append(Finding("permissions_scope", 2 if confirmable else 3, name, "PS-FINANCIAL-ACTION",
                                "Tool moves money or settles payments. "
                                + ("It declares destructiveHint, so clients can prompt for approval." if confirmable
                                   else "No confirmation hint is declared. Irreversible financial actions need human approval.")))
    elif cls in ("write", "delete") and destructive is not True and re.search(IRREVERSIBLE_DESC, desc_text, re.I):
        findings.append(Finding("permissions_scope", 3, name, "PS-IRREVERSIBLE",
                                "Description says the action cannot be undone and no destructiveHint is declared."))

    if cls == "write" and re.search(IDENTITY_FIELDS, " ".join(props).lower()):
        findings.append(Finding("permissions_scope", 2, name, "PS-IDENTITY-CHANGE",
                                "Tool can change contact or credential details (phone, email, password, MFA, beneficiary). In fintech this is a common account-takeover step."))

    for pname, pdef in props.items():
        pl = pname.lower()
        pdef = pdef if isinstance(pdef, dict) else {}
        constrained = any(k in pdef for k in ("enum", "pattern", "maxLength", "format"))
        if pl in PATH_PARAMS and not constrained:
            findings.append(Finding("permissions_scope", 2, name, "PS-OPEN-PATH",
                                    f"Parameter '{pname}' accepts an unconstrained path. Risk of access outside the intended directory."))
        if pl in URL_PARAMS and not constrained:
            findings.append(Finding("permissions_scope", 2, name, "PS-OPEN-URL",
                                    f"Parameter '{pname}' accepts an unconstrained URL or host. Risk of SSRF or data egress."))
        if re.search(r"\bsql\b", pl) and pdef.get("type") == "string":
            findings.append(Finding("output_handling", 3, name, "OH-RAW-QUERY",
                                    f"Parameter '{pname}' looks like a raw SQL string passed to a backend. Check for injection."))
        elif pl == "query" and pdef.get("type") == "string":
            findings.append(Finding("output_handling", 1, name, "OH-SEARCH-QUERY",
                                    f"Parameter '{pname}' is a free-text query. Confirm it is a search expression, not SQL or a shell string."))
        if pdef.get("type") == "string" and not constrained and pl not in PATH_PARAMS | URL_PARAMS:
            findings.append(Finding("output_handling", 1, name, "OH-UNBOUNDED-STRING",
                                    f"Parameter '{pname}' is an unbounded string. Add maxLength, pattern, or enum."))

    schema = tool.get("inputSchema") or {}
    if props and schema.get("additionalProperties") is not False:
        findings.append(Finding("output_handling", 1, name, "OH-OPEN-SCHEMA",
                                "Input schema does not set additionalProperties to false."))


def check_scopes(manifest, findings):
    scopes = manifest.get("scopes") or manifest.get("oauth_scopes") or []
    if isinstance(scopes, str):
        scopes = scopes.split()
    for s in scopes:
        if str(s).lower() in WILDCARD_SCOPES or BROAD_SCOPE_PATTERN.search(str(s)):
            findings.append(Finding("permissions_scope", 3, "<server>", "PS-WIDE-SCOPE",
                                    f"Requested scope '{s}' is wildcard or admin-level."))


def check_server_level(manifest, tools, findings):
    names = [str(t.get("name", "")) for t in tools]
    dupes = {n for n in names if names.count(n) > 1}
    for n in dupes:
        findings.append(Finding("tool_integrity_supply_chain", 2, n, "TI-DUPLICATE-NAME",
                                "Duplicate tool name. Possible shadowing of a trusted tool."))
    if not manifest.get("version") and not (manifest.get("serverInfo") or {}).get("version"):
        findings.append(Finding("tool_integrity_supply_chain", 2, "<server>", "TI-NO-VERSION",
                                "No server version in the manifest. Pin an exact version and hash before approval."))

    # Prompt injection exposure: only a hint. The lethal combination needs human judgment.
    classes = {classify_tool(t) for t in tools}
    ingest = any(re.search(r"\b(fetch|browse|scrape|read[_ ]?(email|mail|issue|ticket|page|url)|search[_ ]?web|inbox|download)\b",
                           f"{t.get('name','')} {t.get('description','')}".lower()) for t in tools)
    egress = any(
        re.search(r"\b(send|post|email|upload|webhook|publish|forward)\b",
                  str(t.get("name", "")).lower().replace("_", " "))
        or re.search(EGRESS_DESC, str(t.get("description", "")), re.I)
        or any(re.fullmatch(OUTBOUND_PARAM, str(pn).lower()) for pn in schema_props(t))
        for t in tools)
    if ingest and egress:
        findings.append(Finding("prompt_injection_exposure", 3, "<server>", "PI-INGEST-PLUS-EGRESS",
                                "Server has tools that read external content AND tools that send data out. Confirm private data is not reachable in the same session. If it is, this is the critical case."))
    elif ingest and classes & {"write", "delete", "exec"}:
        findings.append(Finding("prompt_injection_exposure", 2, "<server>", "PI-INGEST-PLUS-WRITE",
                                "Server reads external content and also has state-changing tools."))
    elif ingest:
        findings.append(Finding("prompt_injection_exposure", 1, "<server>", "PI-INGEST",
                                "Server reads external content. Check that outputs are treated as data."))


# ---------------------------------------------------------------- scoring

def load_rubric(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def draft_scores(rubric: dict, findings):
    out = []
    for crit in rubric["criteria"]:
        cid = crit["id"]
        if cid in SCANNABLE:
            hits = [f for f in findings if f.criterion == cid]
            score = max((f.floor for f in hits), default=0)
            out.append({"id": cid, "name": crit["name"], "hard_gate": crit["hard_gate"],
                        "status": "draft", "score": score, "findings": len(hits)})
        else:
            out.append({"id": cid, "name": crit["name"], "hard_gate": crit["hard_gate"],
                        "status": "MANUAL", "score": None, "findings": 0})
    return out


def draft_verdict(scores):
    """Verdict from scanned criteria only. Only reject is safe to call from a partial scan."""
    gate3 = [s["name"] for s in scores if s["hard_gate"] and s["score"] == 3]
    if gate3:
        return "REJECT (draft)", f"Hard gate at 3: {', '.join(gate3)}."
    manual = [s["name"] for s in scores if s["status"] == "MANUAL"]
    return ("NOT DECIDED", "No hard gate tripped by the manifest, but this scan cannot approve anything. "
            f"Score these manually: {', '.join(manual)}.")


# ---------------------------------------------------------------- main

def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"tools": data}
    if "result" in data and isinstance(data["result"], dict):  # raw JSON-RPC response
        data = {**data["result"], **{k: v for k, v in data.items() if k != "result"}}
    if "tools" not in data:
        raise ValueError("No 'tools' list found. Expected the output of an MCP tools/list call.")
    return data


def scan(manifest: dict):
    findings = []
    tools = manifest["tools"]
    for tool in tools:
        name = str(tool.get("name", "<unnamed>"))
        check_descriptions(tool, name, findings)
        check_capability(tool, name, findings)
    check_scopes(manifest, findings)
    check_server_level(manifest, tools, findings)
    return findings


def render(manifest, findings, scores, verdict, reason):
    lines = []
    lines.append(f"Tools scanned: {len(manifest['tools'])}   Findings: {len(findings)}")
    lines.append("")
    lines.append("DRAFT SCORES (a human must confirm every score)")
    for s in scores:
        gate = " [HG]" if s["hard_gate"] else ""
        val = "MANUAL, needs evidence outside the manifest" if s["score"] is None else f"at least {s['score']}  ({s['findings']} findings)"
        lines.append(f"  {s['name']}{gate}: {val}")
    lines.append("")
    lines.append(f"Draft verdict: {verdict}")
    lines.append(f"  {reason}")
    lines.append("")
    lines.append("FINDINGS")
    for f in sorted(findings, key=lambda x: (-x.floor, x.criterion, x.tool)):
        lines.append(f"  [{f.floor}] {f.rule}  tool={f.tool}  criterion={f.criterion}")
        lines.append(f"      {f.detail}")
    return "\n".join(lines)


def main(argv=None):
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description="Static scanner for MCP tool manifests (draft scoring only).")
    ap.add_argument("manifest", type=Path, help="JSON from an MCP tools/list call")
    ap.add_argument("--rubric", type=Path, default=here.parent / "rubric" / "scoring.yaml")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    try:
        manifest = load_manifest(args.manifest)
        rubric = load_rubric(args.rubric)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    findings = scan(manifest)
    scores = draft_scores(rubric, findings)
    verdict, reason = draft_verdict(scores)

    if args.json:
        print(json.dumps({"scores": scores, "verdict": verdict, "reason": reason,
                          "findings": [asdict(f) for f in findings]}, indent=2))
    else:
        print(render(manifest, findings, scores, verdict, reason))
    return 1 if verdict.startswith("REJECT") else 0


if __name__ == "__main__":
    sys.exit(main())
