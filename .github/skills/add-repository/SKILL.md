---
name: add-repository
description: 'Add a new GitHub repository to this IaC config. Use when: adding a repo, managing a new repository, onboarding a repo, importing an existing repo, creating a new repo with OpenTofu.'
argument-hint: '<repo-name> [existing|new]'
---

# Add a Repository

## When to Use

- Adding a brand-new GitHub repository to the IaC
- Onboarding an existing GitHub repository into OpenTofu state
- Modifying settings of a managed repository

## Procedure

### 1. Create the YAML config file

Create `config/<repo-name>.yaml`. Use the appropriate template below.

**New repository** (OpenTofu creates it):

```yaml
# config/<repo-name>.yaml
name: <repo-name>
description: ""
visibility: private        # public | private | internal
is_template: false
auto_init: true
gitignore_template: null   # e.g. "Terraform", "Python"
license_template: null     # e.g. "mit", "apache-2.0"
topics: []
archived: false
has_projects: false
has_wiki: false
delete_branch_on_merge: true
branch_protection:
  pattern: main
  enforce_admins: false
  require_signed_commits: false
  required_pull_request_reviews:
    required_approving_review_count: 1
```

**Existing repository** (imported into state):

```yaml
# config/<repo-name>.yaml
name: <repo-name>
description: ""
visibility: private
is_template: false
auto_init: false
gitignore_template: null
license_template: null
topics: []
archived: false
has_projects: false        # match actual GitHub setting
has_wiki: false            # match actual GitHub setting
delete_branch_on_merge: false  # match actual GitHub setting
import_id: true
branch_protection: null    # set after import if needed
```

> For an existing repo: fetch the actual settings with `gh api repos/<owner>/<repo-name>` and align all fields to avoid drift.

### 2. Regenerate the tfvars file

```bash
python scripts/generate_tfvars.py
```

This also runs `tofu fmt` automatically.

### 3. Validate the YAML schema

```bash
python scripts/validate_config.py
```

All files must pass before continuing.

### 4. Preview changes

```bash
cd src
tofu plan
```

Review the plan carefully:
- New repo → expect `+ create` actions only.
- Existing repo → expect `1 to import` and minimal or zero `~ update` actions. If there are unexpected updates, adjust the YAML fields to match the actual remote state.

### 5. Open a Pull Request

Commit and push. CI will run validation, `tofu fmt`, `tofu validate`, tests, and plan automatically. Merge to `main` to apply.

## Schema Change Rule

If you need a YAML field that does not exist yet, update **all six locations** together — see the "Schema changes" section in [copilot-instructions.md](../../copilot-instructions.md).
