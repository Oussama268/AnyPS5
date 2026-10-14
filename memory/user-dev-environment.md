---
name: user-dev-environment
description: "User started on an Apple Silicon Mac (relinker only) and moved to a Windows x86-64 PC on 2026-10-14 to build everything and test games; fork Oussama268/AnyPS5"
metadata:
  type: user
---

The user (GitHub `Oussama268`) contributes to AnyPS5 (upstream `boykopovar/AnyPS5`) through the fork `Oussama268/AnyPS5`: locally `origin` is the fork and `upstream` is boykopovar; `main` tracks `upstream/main`. Fork Actions enabled: Build, Conventions, Progress report, Progress comment. Hourly bots are off (fork default); Progress, Labels and Release were disabled at the user's request.

Machines: an Apple Silicon MacBook (M1 Pro, 16 GB) can only build the relinker (`-DANYPS5_RELINKER_ONLY=ON`). On 2026-10-14 the user moved to a Windows x86-64 PC to build everything and test converted games in real time (run, read the terminal error, fix, repeat). The PC's CPU, GPU and RAM had not been recorded yet.

**Why:** running games and building system libraries and shaders needs x86-64 Windows or Linux.

**How to apply:** on the Windows PC do everything locally (WinLibs GCC 15.2.0 exactly). The fork CI still works for a second opinion on Linux: open a PR inside the fork and run `gh workflow run build.yml -R Oussama268/AnyPS5 -f pr=<N>`. Pass `-R boykopovar/AnyPS5` only for real upstream actions, after asking. Related: [[upstream-pr-limit]], [[run-steps-directly]].
