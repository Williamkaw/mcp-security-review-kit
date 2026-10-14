# Rubric

[`rubric.md`](rubric.md) is the human-readable rubric. [`scoring.yaml`](scoring.yaml) is the same criteria in machine-readable form, read by the scanner.

**Scoring:** 8 criteria, each scored 0 (minimal) to 3 (critical), total 0 to 24. Criteria 1 to 4 are hard gates: a 3 on any of them is an automatic reject.

| Verdict | Rule |
|---|---|
| Reject | Any hard gate at 3, or total 15 or more |
| Approve with conditions | Total 7 to 14. Each criterion scored 2 needs a control, an owner and a due date |
| Approve | Total 0 to 6 and no criterion above 1 |

**How to use it:** collect the evidence listed under each criterion, pick the level whose description fits, and write one line of evidence a second reviewer could check. If the evidence is missing, write "Not assessed". Do not guess.

**Known gaps found in the worked reviews:** the rubric scores one server, but prompt injection risk depends on everything in the same session, and some servers score differently under different configurations. The decision record template now asks for both. The thresholds are untested beyond three reviews.
