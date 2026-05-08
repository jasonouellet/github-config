# github-config

Infrastructure as Code (IaC) for managing GitHub repositories in this organization.

## Overview

This repository uses OpenTofu as the IaC engine to manage GitHub repository settings declaratively.
Repository configurations are stored as YAML files, a script generates the IaC
variable file, and GitHub Actions CI/CD pipelines validate and apply changes automatically.

## Directory Structure

```
.
├── .devcontainer/                  # Dev Container configuration (VS Code / GitHub Codespaces)
│   └── devcontainer.json
├── .github/
│   └── workflows/
│       ├── ci.yml                  # CI: schema validation, format, validate, test, plan on PRs
│       └── cd.yml                  # CD: apply on merge to main
├── config/                         # One YAML file per managed GitHub repository
│   ├── github-config.yaml
│   └── example-service.yaml
├── schemas/
│   └── repository.schema.json      # JSON Schema (draft-07) for config/ YAML files
├── scripts/
│   ├── generate_tfvars.py          # Generates src/repositories.auto.tfvars from config/
│   └── validate_config.py          # Validates config/ YAML files against the schema
├── sonar-project.properties        # SonarCloud project configuration
├── src/                            # Root IaC configuration
│   ├── main.tf                     # Calls github_repository module for every repository
│   ├── variables.tf                # Input variable definitions
│   ├── outputs.tf                  # Output definitions
│   ├── terraform.tf                # Provider + backend configuration
│   └── modules/
│       └── github_repository/      # Reusable module: manages one GitHub repository
│           ├── main.tf
│           ├── variables.tf
│           └── outputs.tf
└── test/                           # IaC native tests (.tftest.hcl)
    ├── github_repository.tftest.hcl
    └── root_module.tftest.hcl
```

## Prerequisites

- [OpenTofu](https://opentofu.org/docs/intro/install/) >= 1.6
- Python >= 3.10 with `pyyaml` and `jsonschema` installed (`pip install pyyaml jsonschema`)
- [pre-commit](https://pre-commit.com/) installed (`pip install pre-commit`)
- A GitHub Personal Access Token with `repo` and `admin:org` scopes

## Pre-commit

Install and enable Git hooks locally:

```bash
pre-commit install
```

Run all hooks manually:

```bash
pre-commit run --all-files
```

## YAML Schema Validation

Repository config files in `config/` are validated against `schemas/repository.schema.json`
(JSON Schema draft-07). Validation is **blocking** in CI and also runs automatically via
pre-commit on every staged `config/*.yaml` change.

### Run validation locally

```bash
python scripts/validate_config.py
```

To also produce a Sonar-compatible generic issue report:

```bash
python scripts/validate_config.py --report reports/sonar-issues.json
```

Note: files named `example*.yaml` are ignored by `scripts/generate_tfvars.py` and are treated as examples only.

All options:

| Option | Default | Description |
|--------|---------|-------------|
| `--config-dir DIR` | `config` | Directory with YAML config files |
| `--schema FILE` | `schemas/repository.schema.json` | Path to JSON Schema file |
| `--report FILE` | *(none)* | Write a Sonar-compatible generic issue report to FILE |

### Fixing validation errors

Each error line shows the YAML field path and a description, for example:

```
[FAIL] config/my-repo.yaml
       - visibility: 'staging' is not one of ['public', 'private', 'internal']
       - branch_protection.required_approving_review_count: 10 is greater than the maximum of 6
```

Fix the flagged fields in the YAML file to match the allowed values described in the
[YAML Config Reference](#yaml-config-reference) below.

### Schema versioning

The schema version is noted in the `description` field of `schemas/repository.schema.json`.
Bump the version string whenever the schema gains new constraints or breaking changes.

### Sonar integration

SonarCloud is configured via `sonar-project.properties`. The CI `yaml-validate` job
produces `reports/sonar-issues.json` (Sonar Generic Issue Data format) and then runs
the SonarCloud scan, which picks up both Python analysis of `scripts/` and the external
YAML validation issues.

To enable the SonarCloud scan, add a `SONAR_TOKEN` secret to the repository
(Settings → Secrets and variables → Actions).

## Changelog and Versioning

This repository follows:

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) in [CHANGELOG.md](CHANGELOG.md)
- [Semantic Versioning](https://semver.org/)
- Conventional Commit messages for automatic semantic bump detection

Version bump rules:

- `feat:` -> minor
- `feat!:` or `BREAKING CHANGE:` -> major
- `fix:` -> patch

Release flow on `main`:

1. CI succeeds.
2. Release workflow calculates next version with GitVersion.
3. Workflow validates that `CHANGELOG.md` contains `## [x.y.z]` for that version.
4. Workflow creates and pushes tag `vx.y.z`.
5. Workflow publishes a GitHub Release using the matching changelog section.

When preparing a release, move relevant entries from `## Unreleased` to a new dated version section in `CHANGELOG.md`.

## Adding or Updating a Repository

1. Create or edit a YAML file in `config/` (one file per repository):

```yaml
# config/my-new-repo.yaml
name: my-new-repo
description: "My new repository."
visibility: private          # public | private | internal
auto_init: true
import_id: true            # optional: set true when repo already exists and must be imported
topics:
  - my-topic
branch_protection:
  pattern: main
  require_signed_commits: false
  required_pull_request_reviews:
    required_approving_review_count: 1
```

2. Regenerate the tfvars file:

```bash
python scripts/generate_tfvars.py
```

3. Preview the changes:

```bash
cd src
tofu init
tofu plan
```

4. Open a Pull Request — CI will run `tofu fmt`, `validate`, tests, and `plan` automatically.

5. Merge the PR — CD applies the changes to GitHub.

## YAML Config Reference

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `name` | string | *filename* | Repository name (defaults to the YAML filename without extension) |
| `description` | string | `""` | Short description |
| `visibility` | string | `"private"` | `public`, `private`, or `internal` |
| `is_template` | bool | `false` | Mark as a template repository |
| `auto_init` | bool | `true` | Initialize with a README |
| `gitignore_template` | string | `null` | e.g. `"Terraform"`, `"Python"` |
| `license_template` | string | `null` | e.g. `"mit"`, `"apache-2.0"` |
| `topics` | list | `[]` | Repository topics |
| `archived` | bool | `false` | Archive (make read-only) the repository |
| `import_id` | bool | `null` | Set to `true` to import an existing repo into OpenTofu state before apply |
| `branch_protection` | object | `null` | See below |

### branch_protection

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pattern` | string | `"main"` | Branch name pattern |
| `enforce_admins` | bool | `false` | Enforce rules for admins |
| `require_signed_commits` | bool | `true` | Require GPG-signed commits |
| `required_status_checks.strict` | bool | `true` | Require up-to-date branch |
| `required_status_checks.contexts` | list | `[]` | Required CI check names |
| `required_pull_request_reviews.dismiss_stale_reviews` | bool | `true` | Dismiss stale approvals on new commits |
| `required_pull_request_reviews.require_code_owner_reviews` | bool | `false` | Require CODEOWNERS review |
| `required_pull_request_reviews.required_approving_review_count` | number | `1` | Minimum approvals required |

## Running Tests

Tests use the IaC built-in test framework (OpenTofu >= 1.6 required):

```bash
cd src
tofu init -backend=false
cp ../test/*.tftest.hcl .
tofu test
```

## GitHub Actions Secrets & Variables

| Name | Type | Description |
|------|------|-------------|
| `TF_GITHUB_TOKEN` | Secret | GitHub PAT used by IaC (`repo` + `admin:org` scopes) |
| `GITHUB_OWNER` | Variable | GitHub organization or username |

## Dev Container

Open the repository in VS Code and choose **Reopen in Container** (or use GitHub Codespaces).
The dev container includes:

- IaC tooling (OpenTofu) + TFLint
- Python 3.12 + PyYAML + Ruff
- GitHub CLI
- VS Code extensions: HashiCorp Terraform, Python, Ruff, YAML, GitHub Actions, GitLens
