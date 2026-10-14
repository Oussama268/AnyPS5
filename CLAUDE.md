# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

**Never commit this file.** `tools/check_conventions.py` rejects `CLAUDE.md`, `AGENTS.md` and other agent files anywhere in the tree (`notes-file` rule), which fails the pull request's Conventions check.

Session handoff from the user's previous machine (who they are, what is set up, next steps): @HANDOFF.md

## Project

AnyPS5 ports PS5 executables to native x86-64 Linux ELF or Windows PE programs without emulation. The relinker rewrites the game executable and its bundled modules so that the host OS loader binds their imports, by NID, to native reimplementations of the PS5 system libraries (`.prx` shared libraries built from `core/libs/prx`). GPU command buffers execute on Vulkan, and RDNA shaders are recompiled to SPIR-V. Unsupported or unexpected states throw `std::runtime_error`, which is printed to stderr and terminates the process.

References: `CONTRIBUTING.md` (rules), `docs/dev/ARCHITECTURE.md` (pipeline diagrams), `docs/dev/BUILD.md`, `docs/user/USAGE.md` (relinker CLI, runtime layout, import audit), `docs/dev/TechnicalDebt.md` and `docs/dev/debt/<library>.md` (known gaps, silent stubs, unknown NIDs and signatures; entries about one library go in its `debt/` file).

## Build and test

Relinker only: needs no submodules, system libraries or GPU, and works on Linux, Windows and macOS (including Apple Silicon). It is the only build possible on macOS, and it is enough for relinker changes:

```sh
cmake -S . -B build-relinker -G Ninja -DCMAKE_BUILD_TYPE=Release -DANYPS5_RELINKER_ONLY=ON -DBUILD_TESTING=ON
cmake --build build-relinker --parallel
ctest --test-dir build-relinker --output-on-failure
```

Full build, required for system library and shader changes. x86-64 only: Linux with GCC (SDL needs `libx11-dev` and `libxext-dev`), or Windows with exactly WinLibs MinGW-w64 GCC 15.2.0 (`x86_64-ucrt-posix-seh`, release `15.2.0posix-14.0.0-ucrt-r7`). Configuring downloads FFmpeg binaries unless `FFMPEG_PREBUILT_DIR` is set.

```sh
git submodule update --init --recursive
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=ON -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++
cmake --build build --parallel
cmake --build build --target libs --parallel
ctest --test-dir build --output-on-failure --parallel 4
```

- Every library is `EXCLUDE_FROM_ALL`. The `libs` target NID-patches them into `build/core/libs/libs/*.prx`, the files converted titles load; without it a title runs the previous binaries. The unpatched builds, which tests link against, are in `build/core/libs/libs/unpatched/`.
- The relinker is built at `<build>/core/relinker/relinker`; test executables go to `<build>/tests/`.
- One test: `ctest --test-dir build -N` lists the names. Build its executable (`<name>_tests` by convention) with `cmake --build build --target <name>_tests`, then run `ctest --test-dir build -R '^<name>$' --output-on-failure`.
- Exit code 77 means skipped. Vulkan tests skip without a usable device unless `ANYPS5_REQUIRE_VULKAN=1` is set; CI sets it and runs them on lavapipe. CI's Linux job also configures with `-DANYPS5_ENABLE_SPIRV_TOOLS=ON`.
- Python 3 is optional; without it the Python tests are not registered.
- Other CMake flags are listed in `docs/dev/BUILD.md`.

Checks that CI runs, runnable locally (the conventions check reads commits between the merge base and `HEAD`, not the working tree):

```sh
python3 tools/check_conventions.py --base origin/main    # add --title "<PR title>" --body <file> to check the PR text
python3 tools/check_test_registration.py build           # fails when a built test executable has no ctest test; Ninja build dirs only
```

To run a converted title: `relinker [--windows] [--to-intel] input.elf app.elf`, copy `build/core/libs/libs/*.prx` into `libs/` beside the output, and put the title's resources in `app0/` (`docs/user/USAGE.md`). `relinker --registry` followed by `tools/import_audit.py` classifies a title's imports as implemented, throwing stubs or absent. User settings are `ANYPS5_*` environment variables (`docs/user/`); debug and trace switches are `APS5_*` variables read with `std::getenv`.

## Architecture

### Relinker (`core/relinker`)

C++20 standard library only. `main.cpp` runs the stages in order: optional `--to-intel` lowering of AMD-only x86 instructions (`codegen/`); `RelinkerPipeline`, which reads imports by NID, scans syscalls, filters unused NIDs and builds the SysV dynamic section (`relinker/`); `GuestModuleBuilder`, which converts the title's bundled `sce_module/` modules; then `LinuxElfPatcher` or `WindowsPePatcher` (`elfpatcher/`). Components sit behind `I*` interfaces created by `Make*` factories. `core/relinker/CMakeLists.txt` lists every source explicitly, and most unit-test executables compile the sources they need directly, so a new `.cpp` goes into `relinker` and into each test target that uses it. Tests are C++ programs in `*/tests/` and Python scripts `relinker/tests/test_*.py` that run the built relinker.

### System libraries (`core/libs/prx/<module>`)

- Each directory builds one shared library, `<module>.prx`, named after the module titles import, so variants such as `libSceFont`, `libSceFont.native` and `libSceFont-module` are separate directories (sharing sources through `libSceFont/FontLibrary.cmake`). A directory without `CMakeLists.txt` builds its `Export.cpp` alone. Libraries link `libkernel` and `libc`; `libc` holds the shared runtime (guest heap, guest path resolution, `APS5_LOG_*`, `NotImplemented_nid_no_patch`). Shared PS5 ABI types are in `core/libs/SceTypes.hpp`.
- Exports are functions in `extern "C"` blocks, marked `APS5_VABI` and named by their PS5 name. C++ methods are written the same way, named by their Itanium-mangled name with `this` as the first parameter (see `libSceJson2/Export.cpp`). `APS5_VABI` is `sysv_abi` on Windows and empty elsewhere: leaving it off an export or a guest callback pointer type compiles everywhere and breaks only on Windows.
- After linking, `nid_patcher` (`core/libs/nid`) renames each export to the NID hashed from its name. Suffixes control this: `_nid_postfix` (and `_nid_disambig<N>`) are stripped before hashing, for names that would clash with host symbols; `_nid_no_patch` keeps a symbol out of NID patching (helpers shared between libraries); `<name>_nid_no_patch_cut` is exported as `<name>` verbatim, which is how `APS5_EXPORT("<nid>", func)` exports a known NID whose name is unknown.
- An export belongs in the library the title names for it: Linux resolves a NID from any loaded library, but Windows binds it to the named DLL, so a misplaced export can fail there.
- Unimplemented exports call `NotImplemented_nid_no_patch(__func__)`, which throws.
- Tests: `core/libs/tests/Guest*.cpp` are plain `main()` programs, with no test framework, that call exports by name against the unpatched library and `abort()` on failure. Each is registered in its library's `CMakeLists.txt` with `add_test_executable` and `add_test`, calls `configure_windows_unwind(<target>)`, and on `WIN32` prepends the library's directory to `PATH` through `ENVIRONMENT_MODIFICATION`; copy an existing one.

### Graphics (`libSceAgc`, `libSceAgcDriver`, `core/shader/recompiler`)

`libSceAgc` builds command buffers and `libSceAgcDriver` executes them: `Submit` (DCB/ACB) → `Execution` (PM4 state, draws, dispatches) → `Graphics` (Vulkan). `core/shader/recompiler` translates RDNA shaders (the PS5 GPU is gfx1013, RDNA2): `RdnaDecoder` → `ControlFlow` (graph, structurize) → `Translation` (RDNA to IR) → `Optimization` (SSA, resources, bindings) → `SpirvBackend`, in the order `Recompiler.cpp` runs them.

- The recompiler is isolated from the rest of the project and is a pure function of its input. It is built as the static library `shader_recompiler_agc_driver` by `add_shader_recompiler()`, which libSceAgcDriver's CMake calls.
- Compiled variants are cached in memory and on disk. The disk cache key hashes every recompiler source, the submodule commits, the compiler and flags, and the `"APS5_*"` switch names in those sources. `ShaderCacheVersion.cmake` fails the build when a recompiler source includes a project file outside the recompiler that is not in `shaderCacheKeySources`, or when libSceAgcDriver code calls a `ShaderRecompiler::` function missing from `shaderCacheReviewedNames`, imports the whole namespace, or calls `setenv`/`putenv`. `ANYPS5_NO_SHADER_CACHE=1` disables the disk cache; the tests set it.
- Tests live in `libSceAgcDriver/tests/`. Every `tests/execution/FooBar.cpp` is registered automatically as the ctest test `agc_driver_foo_bar`; these run RDNA code on Vulkan and compare the results with rows measured on hardware. They run from the source root.
- `tools/hw-oracle/` runs RDNA assembly on a local AMD GPU (Linux, `amdgpu`, ROCm HSA runtime) to settle instruction semantics; see `docs/dev/HW_ORACLE.md`.

## Rules

Enforced in review, and on added or changed lines by `tools/check_conventions.py`:

- No comments in C++, Python or CMake. Comments only mark technical debt, are added only by humans, and pass the check only when the pull request also changes `docs/dev/TechnicalDebt.md` or a file in `docs/dev/debt/`. Always allowed: `#endif // X` and `} // namespace X`. Existing comments (many in libSceAgcDriver) are not precedent, and editing or moving a commented line trips the check.
- Every function does exactly what it should or throws. An `sce*` export whose body only discards its arguments and returns a constant is a silent stub; it is allowed only when it unblocks a title and affects only UI, and it must be listed under Silent stubs in its library's `docs/dev/debt/<library>.md`. Missing imports fail at startup, with no fallbacks that keep running. Cases the sources do not settle throw.
- General behaviour only: title IDs (`PPSA12345`, `CUSA12345`) are rejected in non-test `core/` code. Do not reimplement modules that titles ship in `sce_module/`, `sce_modules/` or `prx/` (middleware such as FMOD or Cohtml, SDK wrappers such as NpCppWebApi); only system libraries that reach the kernel or hardware belong in `core/libs/prx`.
- One definition per export across libraries; if removing a duplicate leaves a library without exports, use `APS5_DUMMY_FUN`.
- Standard C++: no `__attribute__`, `__declspec`, or `#pragma` other than `#pragma once`; use the existing macros.
- Third-party code is a submodule under `3rdparty/` built from source. No `find_package` (except Python3, Threads and Git), `find_library` or `pkg_check_modules` outside `cmake/SystemDeps.cmake`, which only `-DANYPS5_USE_SYSTEM_DEPS=ON` uses.
- Pull requests that change shader instruction semantics cite their source: a hardware measurement (which GPU, what was checked) or the exact ISA section, LLVM, ACO or Mesa file. Behaviour not verified on hardware is recorded as technical debt.
- Tests: none that only check that an export exists. Each test finishes in 30 s on CI, Vulkan tests included (lavapipe, no shader cache, ctest in parallel); split or shrink a slow test instead of raising its timeout. Every built test executable must be registered with ctest.
- Repository files are UTF-8 text only, with no images. New `.md`, `.log`, `.patch` or similar files are allowed only under `docs/dev/`, `docs/user/` and `.github/`; investigation notes go in the pull request, and gaps, unknown NIDs and signatures go in technical debt (`docs/dev/debt/<library>.md`). Relative Markdown links must resolve. Documentation is dry, strict and concise. `.gitignore` ignores `*.json`, `*.png`, `*.jpg`, `*.bat` and `*.log` everywhere.
- Naming (`docs/dev/CONVENTIONS.md`): interfaces start with `I`; classes and public methods use PascalCase; private methods, fields and arguments use camelCase; template parameters are named like `TKey` and `TValue`.
- Commit subjects and pull request titles follow Conventional Commits (`feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert`, optional scope). Scopes in use: `shader`, `agc`, `relinker`, `libc`, `libkernel`, `libs`, `tests`, `ci`, `build`, or a library name, as in `fix(libSceAmpr): ...`.
- One topic per branch and pull request, based on current `main`. The description fills `.github/pull_request_template.md`: non-empty What, Tested and Checklist sections, every box checked, `Depends on: #N` or `none`, `Unblocks: <title ID> #<Game bring-up discussion>` or `none`, `GPUs tested:` (vendor, model, driver, OS for AGC, shader or VideoOut changes, else `n/a`), and `AI-assisted: yes|no`.
- Open pull requests per author are capped by merged ones: 1 with none merged, 20 with at least 1, unlimited from 20. Over the cap, `.github/workflows/pr-intake.yml` closes the pull request. Per-title progress is tracked in Game bring-up discussions (https://github.com/boykopovar/AnyPS5/discussions/categories/game-bring-up).

CI: the Conventions check runs on every pull request. Full Linux and Windows builds run on pushes to `main`, and for a pull request only when a collaborator with write access dispatches the Build workflow with its number. The relinker matrix (Linux, Windows, macOS) runs automatically on pull requests whose author already has a commit in `main`. Builds use the pull request merged into current `main`, so a conflicting pull request must be rebased first.
