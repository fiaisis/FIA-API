# AGENTS.md

Guidance for coding agents working in this repository.

## What this repo is

`fia-api` is the ReST API for the Flexible Interactive Automation (FIA) system. It's a FastAPI
application backed by PostgreSQL (via SQLAlchemy), with optional Redis/Valkey caching and RabbitMQ
messaging. See `README.md` for env vars, running instructions, and an overview of transforms and the
repository/specification data access pattern — read it before making changes.

## Position in the FIA service

### Overarching FIA architecture

FIA is a multi-repository system (all checked out as siblings under the same parent workspace
directory) that automatically reduces instrument data, and also lets users browse, plot, and rerun
that data interactively:

```text
[ISIS Instrument Archive (/archive, /imat) & lastrun.txt]
        │
        ▼
  file-watcher (Kopf Operator + Per-Instrument Watcher Pods)
        │  publishes file path to RabbitMQ: `watched-files`
        ▼
  run-detection ◄──── fetches instrument rules (`GET /instrument/{inst}/specification`) ────► FIA-API (THIS REPO)
        │  ingests .nxs metadata, verifies rules, publishes JobRequest JSON
        │  to RabbitMQ: `scheduled-jobs` (or retries via `failed-watched-files`)
        ▼
  jobcontroller (job_creator) ◄──── requests PreScript (`GET /script/{inst}`) & posts Job ──► FIA-API ◄──► autoreduction-scripts
        │  spawns Kubernetes Job in cluster:
        ├──► Main container: runners (`ghcr.io/fiaisis/mantid` or `mantid-imaging`) -> writes reduced data to `/ceph`
        └──► Sidecar container: jobcontroller (job_watcher) -> updates job status/outputs in FIA-API (`PATCH /job/{id}`)

[Interactive / Web & Live Data Paths]
  scigateway (Host App) ──► frontend (FIA React Plugin)
                                ├──► fia-auth (UOWS login, JWT verify/refresh, `/experiments` RB lookup)
                                ├──► FIA-API (THIS REPO) (runs, jobs, scripts, specifications, reruns -> `watched-files` / `scheduled-jobs`)
                                └──► plotting-service (h5grove NeXus/HDF5 & IMAT image serving from `/ceph` & `/imat`)

  Kafka (`<INST>_events`, `<INST>_sampleEnv`, `<INST>_runInfo`)
        └──► live-data (Live Data Operator + Mantid Live Data Processor fetching `/live-data/{inst}/script` from FIA-API)

  LLSP (Long Lived Script Processors: `LLSP-API` + RabbitMQ + Celery `LLSP-Worker` built on `ghcr.io/fiaisis/mantid`)

[Infrastructure & Deployment]
  k8s (Terraform + Ansible for OpenStack clusters, Redpanda, local Minikube)
  gitops (ArgoCD App-of-Apps & Kustomize `base`/`envs`/`variants` manifests for all FIA services)
```

### This repository's location (upstream, downstream & siblings)

- **Role**: `fia-api` is the central REST API and Postgres-backed system of record for the FIA
  service — runs, jobs, reductions, scripts/transforms, and instrument specifications all live
  here, and almost every other FIA component talks to it directly.
- **Upstream callers (who calls `fia-api`)**:
  - `run-detection` (`../run-detection`) — fetches `GET /instrument/{instrument}/specification` to
    verify and enrich detected runs.
  - `jobcontroller`'s `job_creator` (`../jobcontroller`) — fetches `GET /script/{instrument}` to
    build job scripts, and posts job records.
  - `jobcontroller`'s `job_watcher` (`../jobcontroller`) — updates job status/outputs via
    `PATCH /job/{id}`-style endpoints as jobs complete.
  - `frontend` (`../frontend`) — the FIA SciGateway plugin; lists/searches runs, jobs, and reruns
    through this API.
  - `live-data` (`../live-data`) — the Live Data Processor fetches live reduction scripts via
    `GET /live-data/{instrument}/script`.
- **Downstream callees (who/what `fia-api` calls or publishes to)**:
  - `fia-auth` (`../fia-auth`) — JWT verification and experiment (RB number) lookups for
    authenticated requests (see `core/auth/`).
  - RabbitMQ `watched-files` queue — resubmitting/rerunning jobs (`core/job_maker.py`) feeds back
    into the same queue consumed by `run-detection`.
  - Postgres — primary datastore (`core/models.py`, `core/repositories.py`).
  - Redis/Valkey — optional caching layer (`core/cache.py`).
  - `/archive` and `/imat` mounts — resolving a run's bare filename to its full archive path (see
    `ARCHIVE_DIR`/`IMAT_DIR` env vars and `core/utility.py`).
- **Sibling repositories to check when changing contracts**: `../run-detection` (specification JSON
  shape), `../jobcontroller` (script/job payload shape), `../autoreduction-scripts` (scripts served
  via transforms), `../frontend` (any REST response shape consumers), `../fia-auth` (auth/JWT
  contract), `../live-data` (live script endpoint), and `../gitops` (deployment manifests/env vars
  for `fia-api`).

### Core technologies
- **Python**: version/minimum is defined by `requires-python` in `pyproject.toml` — do not hardcode a
  version here; always check `pyproject.toml` (and `.github/workflows/`, which may pin a newer CI
  version than the `requires-python` floor) before creating an environment.
- **FastAPI** (`fastapi[all]`): web framework, ASGI app in `fia_api/fia_api.py`
- **SQLAlchemy** + **psycopg2**: ORM/data access against PostgreSQL
- **Pydantic**: request/response models (`core/request_models.py`, `core/responses.py`)
- **PyJWT** / **PyGithub**: auth token handling and GitHub API access (`core/auth/`)
- **redis** (Valkey-compatible): caching (`core/cache.py`)
- **pika**: RabbitMQ producer for job messages (`core/job_maker.py`)
- **OpenTelemetry** (`opentelemetry-*`): tracing/instrumentation
- **Pytest** (+ `pytest-asyncio`, `pytest-cov`, `pytest-random-order`, `pytest-env`, `Faker`, `httpx`): testing
- **Ruff**: linting and formatting
- **Mypy**: type checking, run with `--strict` in CI
- **Docker**: containerization (`container/fia_api.D`)

## Repository structure

```
fia_api/                     Application source package — FastAPI app entrypoint and exception handlers
                              live at the top level
  core/                      Domain logic: SQLAlchemy ORM models, repository + specification pattern
                              data access (query building, filters, pagination), service layer used by
                              routers, auth (JWT tokens, experiment access checks), DB session/engine
                              setup, Redis/Valkey cache helpers, RabbitMQ job publishing, and shared
                              filesystem/path helpers (e.g. safe archive lookups)
  routers/                   FastAPI routers — one module per resource (jobs, instrument, live_data, ...)
  scripts/                   PreScript handling, plus one transform module per instrument (mari, gem,
                              iris, tosca, ...) under scripts/transforms/
local_scripts/               Ad-hoc/dev scripts (not part of the deployed app)

test/                        Pytest test suite, mirroring fia_api/'s structure — unit tests per module,
                              plus e2e/ (needs Postgres/RabbitMQ/Valkey — see tests.yml) and test_ceph/
                              (fixture data mimicking the instrument archive layout)

container/                    Dockerfile
utils/                        Dev tooling (e.g. a script that generates a realistic mock Postgres DB)
examples/                     Example job scripts and env file
.github/workflows/             CI workflows: tests, formatting/linting, build & push, etc.
pyproject.toml, mypy.ini,      Package metadata, dependencies, and ruff/mypy/pytest config — formatting
.pylintrc                      is primarily ruff-driven; see the "pyproject.toml — read this first"
                                section below
```

Routers are thin: they call into `core/services` and `core/repositories`/`specifications` for data
access. When adding a new instrument transform, follow the pattern documented in `README.md`
("Adding New Transforms") — new class in `fia_api/scripts/transforms/`, registered in the
`get_transform_for_instrument` factory.

## pyproject.toml — read this first

`pyproject.toml` is the single source of truth for dependencies, extras, and tool config. Before
adding a dependency, changing supported Python versions, or changing lint/type rules, read it in
full:

- Runtime dependencies are pinned exactly (`==`) under `[project.dependencies]` — keep new
  dependencies pinned the same way.
- Optional extras: `formatting` (ruff, mypy, type stubs), `test` (pytest + plugins), `all` (both).
  Install with e.g. `pip install .[all]` (escape brackets in some shells: `.[all]` -> `.\[all\]`).
- `requires-python` defines the minimum supported Python version — treat it, not this document, as
  the source of truth, and check it before creating an environment. CI's `.github/workflows/` may
  pin a specific (newer) version to actually run against; prefer matching that CI version locally
  when the two differ.
- Ruff config (`[tool.ruff]`, `[tool.ruff.lint]`) enables a large rule set (bandit, bugbear, pylint,
  pyupgrade, pathlib, etc.) with a `line-length = 120`. Run `ruff check` / `ruff format` before
  considering a change done, and check `[tool.ruff.lint.ignore]` and per-file ignores before
  "fixing" something that's intentionally excluded.
- `mypy` is configured via the separate `mypy.ini` (extra) and `.pylintrc` for pylint — both still
  apply alongside ruff. CI runs `mypy --strict fia_api`, so run it the same way locally.
- Pytest config lives under `[tool.pytest.ini_options]` (`required_plugins = "pytest-env"`) — see
  `test/` for `pytest-env`/fixture usage; `--random-order` is used in CI so tests must not depend on
  execution order.

## Environment & running commands

These instructions are deliberately generic: do not assume any particular machine already has a
conda env, kubectl context, or virtualenv set up for this project — check what's actually available
before running anything, and don't hardcode names/paths you happened to see on one machine into
scripts or docs. Everything below is written to work on Linux, macOS, and Windows.

Prefer `conda` when it is available; fall back to a Python `venv` only if conda is not installed.
Check with `command -v conda` (Linux/macOS) or `where conda` (Windows) — never assume either way.

1. Check whether a conda env already exists for this project:
   ```shell
   conda env list
   ```
   If a suitable env already exists (name varies per machine — look for one that matches this repo,
   e.g. containing `fia-api`), use it by name:
   ```shell
   conda run -n <env-name> <command>
   # or, POSIX shells:
   conda activate <env-name>
   # Windows (cmd/PowerShell), after `conda init`:
   conda activate <env-name>
   ```
2. If no suitable conda env exists but `conda` is installed, create one (pick any env name; it does
   not need to match a name used elsewhere):
   ```shell
   conda create -n fia-api python=<version-from-pyproject.toml-or-CI> -y
   conda run -n fia-api pip install .[all]
   ```
3. Only if `conda` itself is not installed, fall back to a virtualenv. Creation is the same
   everywhere; activation differs by OS/shell:
   ```shell
   python3 -m venv .venv        # Linux/macOS (use `python` on Windows)
   ```
   ```shell
   . .venv/bin/activate         # Linux/macOS, POSIX shell
   ```
   ```powershell
   .venv\Scripts\Activate.ps1   # Windows PowerShell
   ```
   ```bat
   .venv\Scripts\activate.bat   # Windows cmd.exe
   ```
   Then, on any OS: `pip install .[all]` (escape the brackets in shells where it's needed, e.g.
   `.\[all\]` in zsh; not needed in bash, PowerShell, or cmd).

Run the app directly (see `README.md` for required env vars, e.g. `DEV_MODE=True` for no-auth local
dev). Replace `conda run -n <env-name>` with the venv-activated shell's plain command if you're using
a virtualenv instead:
```shell
conda run -n <env-name> uvicorn fia_api.fia_api:app --reload
```

Run tests/lint the same way, e.g.:
```shell
conda run -n <env-name> pytest . --random-order --random-order-bucket=global --ignore=test/e2e
conda run -n <env-name> ruff check .
conda run -n <env-name> mypy --strict fia_api
```

Integration/e2e tests additionally need Postgres (and for some suites RabbitMQ/Valkey) running
locally — see `.github/workflows/tests.yml` for the exact services/env vars each job expects
(e.g. Postgres on `localhost:5432`, user `postgres`, password `password`). Note the archive-related
paths mentioned in `README.md`/`fia_api/core/utility.py` (e.g. `/archive`, `/imat`) are Linux-style
paths used by the deployed service/mounts, not necessarily local dev machine paths — don't assume
they exist locally, especially on Windows.

## Kubernetes commands

Available kubectl contexts vary per machine/operator and are not something to assume or hardcode —
always run `kubectl config get-contexts` first to see what's actually configured before targeting a
cluster. Never rely on whatever context happens to be marked current — always pass `--context`
explicitly, and put it at the **end** of the command:

```shell
kubectl get pods -n fia --context <context-name>
kubectl logs deploy/fia-api -n fia --context <context-name>
```

Double- and triple-check the context name before running anything against a production-like
cluster — naming conventions for staging/production contexts differ between machines and operators.

## Managing issues

This repo has no local `.github/ISSUE_TEMPLATE/`; GitHub serves the org-wide default template from
`fiaisis/.github` instead. Always use it rather than inventing an ad hoc issue format:

```shell
gh issue create --template Issue
```

Check `gh issue list` / `gh issue view <number>` first to avoid duplicates.

## Branch naming

Branches use snake_case descriptions of the work being done. Do not use category prefixes like
`feature/` or `fix/`.

- **Format**: `description_of_work` (e.g. `fix_resubmit_watched_files_path`, `add_ngem_transforms`).

## Commit messages

`main`'s history (`git log --oneline main`) is almost entirely **squash merges**: one commit per PR,
titled `<PR title> (#<PR number>)`, e.g. `Fix resubmit_job_to_watched_files publishing bare filename
instead of archive path (#700)`. This has two practical consequences:

- **The PR title is what actually survives into permanent history.** The individual commits you make
  on a working branch are squashed into one commit on merge, so getting the PR title right (see
  "Pull request process" below) matters more than crafting a perfect commit-by-commit history.
- **Individual commit messages still matter for review and for the squash commit body.** By default,
  GitHub's squash merge concatenates every commit subject on the branch into the squashed commit's
  body (visible via `git log -1 --format=%B <commit>` on an existing squash commit). So:
  - Write each commit as a focused, reviewable unit of work with a clear, imperative-mood summary
    line (e.g. `Resolve archive path for resubmit_job_to_watched_files`, `Normalise .nxs extension
    and drop recursive archive search`) — avoid noise like `wip`, `fix`, or `address review comments`
    that would otherwise leak into the squashed body.
  - Add a short body paragraph on non-trivial commits explaining *why*, not just *what*, following the
    style already used in this repo's history (see `git log` on recent feature PRs for examples).
  - Dependabot PR commits are auto-generated and already follow a consistent, verbose format (package
    table + per-dependency changelog links) — leave those as-is rather than editing them.

## Requirements for code changes

Only run tests, linters, and type checkers when they are **relevant to the files you actually
changed** — if a change only touches documentation (e.g. `.md` files), skip `pytest`, `ruff`, and
`mypy`. When you do change Python code, dependency manifests, or configuration, before considering
the change complete:
1. **Add or update unit tests** in the matching `test/` subdirectory for any new or changed
   behavior — don't rely on existing tests happening to cover it.
2. **Add or update e2e tests** in `test/e2e/` when the change affects behavior that suite already
   exercises (e.g. job creation/resubmission, DB-backed flows, queue publishing).
3. **Run the linter, formatter, and type checker** (`ruff check .`, `ruff format .`,
   `mypy --strict fia_api`) and fix everything reported — don't just rely on CI's auto-fix commit.
4. **Run the full test suite with coverage** and confirm coverage has not regressed compared to
   `main` (CI uploads results to Codecov; locally, add `--cov-report=term-missing` to the commands
   in "Environment & running commands" to see uncovered lines before and after your change).

## Pull request process

1. **Local validation** before opening a PR (when `.py` / `pyproject.toml` / workflow files are
   changed; skip for `.md`-only changes) — run against whichever env you set up above:
   ```shell
   conda run -n <env-name> pytest . --random-order --random-order-bucket=global --ignore=test/e2e
   conda run -n <env-name> ruff check .
   conda run -n <env-name> ruff format .
   conda run -n <env-name> mypy --strict fia_api
   ```
   Note: the CI formatting workflow (`formatting_and_linting.yml`) also runs `ruff format .`,
   `ruff check --fix`, and `mypy --strict fia_api` on every push to a non-`main` branch, and
   automatically commits/pushes any fixes back to your branch.
2. **PR title**: a clear, concise description in normal grammar/title case (e.g. `Add GEM Transform`,
   `Remove runno bug`). Do not use snake_case for PR titles.
3. **PR description**: use the org-wide default template from `fiaisis/.github`
   (`.github/pull_request_template.md` — no local override in this repo), which is just
   `Closes # <Issue Number>` followed by a `## Description` section. Ask the user for the issue
   number if one isn't evident from the task, or confirm there is none to link.
4. **AI-assistance label**: attach a label to the PR indicating that it was made with the assistance
   of AI. Check existing labels first with `gh label list` (e.g. `AI` or `AI_code` in this org) and
   apply the matching label via `gh pr create --label <label>` or
   `gh pr edit <number> --add-label <label>`; if the repo does not have an AI label yet, create one
   first (`gh label create "AI" --description "Created with the assistance of AI"`).

## Handling Dependabot PRs

Dependabot creates PRs grouped as `python-packages` (weekly) and `action-packages` (daily, GitHub
Actions) per `.github/dependabot.yml`. When asked to handle these:

1. **List and identify**: `gh pr list` to find open Dependabot PRs.
2. **Review changes**: `gh pr diff <number>`, paying close attention to major version bumps in
   `pyproject.toml`, `container/fia_api.D`, or `.github/workflows/`.
3. **Validate**:
   - Python/dependency changes: `gh pr checkout <number>`, then run the test suite and lint/type
     checks as in the PR process above.
   - Docker/Action changes: check CI results instead of running locally — `gh pr checks <number>`.
4. **Approve and merge** once validation passes:
   ```shell
   gh pr review <number> --approve
   gh pr merge <number> --merge
   ```
   Use `--admin` if the merge is blocked by branch protection (e.g. `gh pr merge <number> --merge --admin`).
5. **Clean up**: close redundant/superseded PRs with `gh pr close <number> --delete-branch`.
6. **Final verification**: after merging, return to `main`, pull, and re-run the unit test suite once
   more to confirm everything is green.

## General working practices

- Prefer the `read` tool (with `offset`/`limit`) over `sed -n`, `cat`, or similar shell one-liners
  when inspecting file contents, and prefer the `write` and `edit` tools over `bash` (`cat <<EOF`,
  `sed -i`, `echo >`), Python one-liners, or other non-tool-based commands whenever creating or
  modifying files.
- Ask the user a clarifying question whenever a task is ambiguous (e.g. which instrument a transform
  applies to, which environment/context a change targets, whether a schema/migration change is in
  scope, or whether an issue number exists to link in a PR) rather than guessing.
- Match existing patterns (repository/specification pattern, router -> service -> repository
  layering, transform factory) rather than introducing new architectural styles.
- Keep dependency versions pinned in `pyproject.toml` consistent with the existing style.

## Keeping this document up to date

If a change you make would make any information in this `AGENTS.md` inaccurate or incomplete —
e.g. a new environment variable, a changed directory layout, a new/renamed CI workflow, an updated
Dependabot grouping, a new sibling-repo contract, or a different testing/linting command — update
the relevant section of this file as part of the same change. Treat it the same way you would treat
`README.md`: documentation that goes stale is worse than no documentation, so don't leave it to a
future agent or PR to notice the drift.
