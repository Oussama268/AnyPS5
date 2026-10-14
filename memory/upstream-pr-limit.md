---
name: upstream-pr-limit
description: "Upstream AnyPS5 caps open PRs by merged count (1 with none merged, 20 with 1+, unlimited from 20); user has 0 merged, so one PR at a time"
metadata:
  type: project
---

Since about 2026-10-14, `.github/workflows/pr-intake.yml` on `boykopovar/AnyPS5` closes a PR opened over the author's open-PR cap: 1 open PR with no merged PRs, 20 with at least 1 merged, no cap from 20 merged. It replaced the 2026-10-09 rule that closed every PR from authors with fewer than 20 merged. As of 2026-10-14 the user has 0 merged PRs.

**Why:** a second open PR from the user is closed automatically until the first is merged or closed.

**How to apply:** re-read `pr-intake.yml` and `CONTRIBUTING.md` on upstream `main` before planning a PR (the repo changes thousands of commits per week). Pick the one most valuable change for the single slot; extra work goes on fork branches or into issues linking a tested fork commit. Search open PRs, issues and the title's Game bring-up discussion right before starting and before posting, because other contributors, many using AI agents, fix the same things within hours (a relinker `.bss` fix of ours was duplicated by #2549/6158444f). Fill the `Unblocks: <title ID> #<discussion>` checklist line for title fixes. Always get the user's approval before posting upstream. Related: [[user-dev-environment]].
