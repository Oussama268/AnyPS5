---
name: run-steps-directly
description: "User wants Claude to execute setup, build and git/gh steps itself instead of listing commands for them to run"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 5784ec87-c0f3-4bb5-8742-11f3ff77232c
  modified: 2026-10-09T14:29:56.377Z
---

When a task involves commands (installs, builds, git or gh setup), run them and report the result rather than handing the user a list of steps.

**Why:** in the 2026-10-09 session the user twice answered instructions with "just do it" / "just run the stuff ur self please".

**How to apply:** execute the steps directly. Still ask before outward-facing actions they haven't approved, such as opening a pull request on upstream `boykopovar/AnyPS5`. Related: [[user-dev-environment]].
