# AnyPS5 handoff (Mac → Windows, 2026-10-14)

Context for Claude Code on the user's Windows PC. This branch (`claude-context`) is an orphan branch on the fork that holds only notes. Never merge it, and never commit `CLAUDE.md` or `HANDOFF.md` to any other branch: upstream's Conventions check rejects agent files.

## Load this on a new machine

From the root of a clone of `Oussama268/AnyPS5`, in PowerShell:

```powershell
git fetch origin claude-context
git restore --source origin/claude-context -- CLAUDE.md HANDOFF.md memory
Add-Content .git/info/exclude "CLAUDE.md`nHANDOFF.md`nmemory/"
```

`git restore --source` writes the files without staging them, and the exclude lines keep them out of `git add -A`. Then:

1. Copy each file in `memory/` into your own auto-memory directory for this project, keeping `MEMORY.md` as the index. Merge with any existing files rather than duplicating them.
2. Delete the `memory/` folder from the clone.
3. To update this branch later, use a separate worktree (`git worktree add ../ctx claude-context`), copy the files in, commit and push. Don't switch the main clone to it.

## Who the user is and how they work

- GitHub user `Oussama268`; git name `Oussama Afassi`.
- New to AnyPS5. The goal is to contribute by testing games and fixing what breaks.
- They want you to run commands yourself, not hand them lists of steps (see `memory/run-steps-directly.md`).
- Ask before anything that posts upstream: PRs, issues and comments on `boykopovar/AnyPS5`.
- They write short, informal messages. Answer plainly.

## What is set up

- The fork `Oussama268/AnyPS5` was synced with upstream `main` on 2026-10-14 (at `28b6f198`).
  - Remotes on the Mac were `origin` = fork and `upstream` = `boykopovar/AnyPS5`. Set up the same on Windows: `git remote add upstream https://github.com/boykopovar/AnyPS5.git`.
  - Branch `main` tracks `upstream/main`.
- Fork Actions are enabled: Build, Conventions, Progress report and Progress comment.
- To get a full Linux + Windows CI build of a change, open a PR inside the fork (base `Oussama268:main`), then run `gh workflow run build.yml -R Oussama268/AnyPS5 -f pr=<N>`.
- Fork branch `perf/windows-zero-fill-tails` is obsolete; upstream merged an equivalent fix in 6158444f. Delete it if the user agrees.
- On the Mac only the relinker-only build worked; its 38 tests passed. Nothing has been built on Windows yet.

## History so far

1. Wrote `CLAUDE.md` (repo guide, untracked).
2. Fuzzed the relinker with ASan/UBSan on the Mac. Found the Windows PE writer storing zero-filled `.bss` tails in the `.exe` (huge files). Fixed it on the fork, and it passed fork CI. Upstream fixed the same issue independently hours earlier (issue #2549, commit 6158444f), so our fork PR #1 was closed. Lesson: search open PRs, issues and discussions right before starting work and again before posting.
3. Upstream PR policy changed twice; the current rule is in `memory/upstream-pr-limit.md`. With 0 merged PRs the user can have 1 open upstream PR. Spend that slot on the best fix.
4. The user decided to move to Windows because game testing needs an x86-64 PC.

## Next steps on Windows

1. **Check the PC.** Record CPU vendor (Intel needs `--to-intel`), GPU and driver (Vulkan 1.1+), RAM and page file size into the user memory note. Use `Get-CimInstance Win32_Processor, Win32_VideoController, Win32_ComputerSystem` and `vulkaninfo --summary` if the Vulkan SDK is installed.
2. **Install the toolchain** (see `docs/dev/BUILD.md`, re-read it since it changes often):
   - Git for Windows, CMake, Ninja, Python 3.
   - Exactly WinLibs MinGW-w64 GCC 15.2.0 (`x86_64-ucrt-posix-seh`, release `15.2.0posix-14.0.0-ucrt-r7`), with its `mingw64\bin` on `PATH` before configuring.
   - Set `SSL_CERT_FILE=C:\Program Files\Git\mingw64\etc\ssl\certs\ca-bundle.crt` for the FFmpeg download at configure time.
   - Point `TEMP`/`TMP` at a folder excluded from antivirus; Defender quarantines relinker test executables otherwise.
3. **Build and test** (commands in `CLAUDE.md`): `git submodule update --init --recursive`, configure, build, the `libs` target, then ctest. Report failures that also fail on upstream CI as known flakes rather than chasing them. `guest_video_out_wqhd_detection` crashed once with 0xc0000374 on CI, related to #2540.
4. **Test a game.** The user supplies their own legally obtained dumps; the project ships none.
   - Convert with `relinker --windows --windows-diagnostics --registry [--to-intel] <dump>\eboot.bin <out>\app.exe`.
   - Lay out `<out>\libs\` (all `build\core\libs\libs\*.prx` plus `libgcc_s_seh-1.dll`, `libstdc++-6.dll`, `libwinpthread-1.dll` from the compiler's `mingw64\bin`), `<out>\app0\` (game files) and the converted `sce_module` files the relinker prints as `Guest module:`.
   - Optional: `anyps5-fonts\` with Noto fonts for system font sets (`docs/user/USAGE.md`).
   - Before launching, run `python tools/import_audit.py <out>\app.registry.json <module registries...> --libs build\core\libs\libs --modules <dump>\sce_module`. It lists unimplemented and missing functions.
   - Run it from a terminal and read the first error. Typically that is `<name> not implemented` (a throwing stub), a missing import at startup, or a `create direct memory backing` failure (enlarge the page file; titles commit up to 13824 MiB).
5. **Fix loop.** For each stop:
   - Check the title's Game bring-up discussion (https://github.com/boykopovar/AnyPS5/discussions/categories/game-bring-up) and search open PRs for the function name. Someone may already have a fix.
   - Implement the general behaviour (never title-specific), with a `core/libs/tests/Guest*.cpp` test when practical.
   - Re-run the game and continue to the next stop.
   - Keep each fix on its own branch from current `upstream/main`.
6. **Upstream.**
   - Pick the strongest single fix for the one PR slot and fill the PR template, including `Unblocks: <title ID> #<discussion>` and `AI-assisted: yes`.
   - Run `python tools/check_conventions.py --base upstream/main` first.
   - Report other stops in the title's bring-up discussion or as issues with the commit hash, OS, GPU, title ID and version, and the `sce_module/` listing.
   - Get the user's OK before posting anything.
