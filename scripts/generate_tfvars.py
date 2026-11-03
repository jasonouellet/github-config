#!/usr/bin/env python3
"""
generate_tfvars.py

Reads all YAML files from the config/ directory and generates a
repositories.auto.tfvars file consumed by OpenTofu in src/.

Usage:
    python scripts/generate_tfvars.py [--config-dir CONFIG_DIR] [--output OUTPUT]

Options:
    --config-dir    Directory containing YAML repository config files
                    (default: config)
    --output        Path for the generated tfvars HCL file
                    (default: src/repositories.auto.tfvars)
"""

import argparse
import copy
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "Error: PyYAML is required. Install it with: pip install pyyaml",
        file=sys.stderr,
    )
    sys.exit(1)


SCHEMA_DEFAULTS = {
    "description": "",
    "visibility": "private",
    "is_template": False,
    "auto_init": True,
    "gitignore_template": None,
    "license_template": None,
    "topics": [],
    "archived": False,
    "has_projects": False,
    "has_wiki": False,
    "delete_branch_on_merge": True,
    "has_issues": True,
    "allow_merge_commit": False,
    "allow_rebase_merge": True,
    "merge_commit_title": None,
    "merge_commit_message": None,
    "squash_merge_commit_title": None,
    "squash_merge_commit_message": None,
    "import_id": None,
    "rulesets": [],
    "code_scanning": {
        "require_sonarcloud": False,
        "require_trivy": False,
    },
}

RULESET_DEFAULTS = {
    "name": "main",
    "target": "branch",
    "enforcement": "active",
    "import_id": None,
    "bypass_actors": [],
    "conditions": {
        "ref_name": {
            "include": ["~DEFAULT_BRANCH"],
            "exclude": [],
        }
    },
    "rules": {
        "creation": None,
        "update": None,
        "deletion": None,
        "required_linear_history": None,
        "required_signatures": None,
        "non_fast_forward": None,
        "update_allows_fetch_and_merge": None,
        "pull_request": None,
        "required_status_checks": None,
        "required_code_scanning": None,
        "copilot_code_review": None,
    },
}

RULESET_PULL_REQUEST_DEFAULTS = {
    "dismiss_stale_reviews_on_push": False,
    "require_code_owner_review": False,
    "require_last_push_approval": False,
    "required_approving_review_count": 0,
    "required_review_thread_resolution": False,
    "allowed_merge_methods": ["merge", "squash", "rebase"],
    "required_reviewers": [],
}

RULESET_REQUIRED_STATUS_CHECKS_DEFAULTS = {
    "strict_required_status_checks_policy": True,
    "do_not_enforce_on_create": False,
    "required_check": [],
}

RULESET_REQUIRED_CODE_SCANNING_DEFAULTS = {
    "required_code_scanning_tool": [],
}

RULESET_COPILOT_CODE_REVIEW_DEFAULTS = {
    "review_on_push": False,
    "review_draft_pull_requests": False,
}

CODEQL_REQUIRED_TOOL = {
    "tool": "CodeQL",
    "security_alerts_threshold": "high_or_higher",
    "alerts_threshold": "errors",
}

TRIVY_REQUIRED_TOOL = {
    "tool": "Trivy",
    "security_alerts_threshold": "high_or_higher",
    "alerts_threshold": "errors",
}

SONARCLOUD_REQUIRED_CHECK = "SonarCloud Code Analysis"

# Ruleset applied to every repository that does not declare `rulesets`.
# A ruleset named "main" in a config file is deep-merged over this one.
DEFAULT_MAIN_RULESET = {
    "name": "main",
    "bypass_actors": [
        {"actor_id": 5, "actor_type": "RepositoryRole", "bypass_mode": "always"}
    ],
    "rules": {
        "deletion": True,
        "required_signatures": True,
        "pull_request": {
            "required_review_thread_resolution": True,
            "allowed_merge_methods": ["rebase", "squash"],
        },
        "required_code_scanning": {
            "required_code_scanning_tool": [CODEQL_REQUIRED_TOOL]
        },
        "copilot_code_review": {},
    },
}

HCL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")


def merge_defaults(data: dict, defaults: dict) -> dict:
    """Return a new dict that is defaults overridden by data."""
    result = {**defaults}
    for key, value in data.items():
        if key in result:
            result[key] = value
    return result


def deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge override into base; lists and scalars are replaced."""
    result = copy.deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def with_default_rulesets(
    rulesets_data: list[dict] | None,
    code_scanning_options: dict | None = None,
) -> list[dict]:
    """Apply the default "main" ruleset.

    An omitted `rulesets` key yields the default ruleset, an explicit empty
    list opts out, and a ruleset named "main" overrides the default one.
    CodeQL remains required by every default or customized "main" ruleset.
    """
    if rulesets_data is None:
        rulesets = [copy.deepcopy(DEFAULT_MAIN_RULESET)]
    else:
        rulesets = [
            deep_merge(DEFAULT_MAIN_RULESET, ruleset)
            if ruleset.get("name", "main") == DEFAULT_MAIN_RULESET["name"]
            else ruleset
            for ruleset in rulesets_data
        ]

    if code_scanning_options is None:
        options = {}
    elif isinstance(code_scanning_options, dict):
        options = code_scanning_options
    else:
        raise TypeError("code_scanning options must be a mapping")

    require_sonarcloud = options.get("require_sonarcloud", False)
    require_trivy = options.get("require_trivy", False)
    if not isinstance(require_sonarcloud, bool) or not isinstance(require_trivy, bool):
        raise TypeError("code_scanning options must be booleans")

    main_rulesets = [
        ruleset
        for ruleset in rulesets
        if ruleset.get("name", "main") == DEFAULT_MAIN_RULESET["name"]
    ]
    if (require_sonarcloud or require_trivy) and not main_rulesets:
        raise ValueError(
            "code_scanning options require a 'main' ruleset; "
            "they cannot be used with rulesets: [] or without a 'main' ruleset"
        )

    for ruleset in main_rulesets:
        rules = ruleset.setdefault("rules", {})
        if rules is None:
            rules = {}
            ruleset["rules"] = rules
        if not isinstance(rules, dict):
            raise TypeError("main ruleset rules must be a mapping")

        required_scanning = rules.get("required_code_scanning")
        if required_scanning is None:
            required_scanning = {}
            rules["required_code_scanning"] = required_scanning
        if not isinstance(required_scanning, dict):
            raise TypeError("required_code_scanning must be a mapping")

        required_tools = required_scanning.get("required_code_scanning_tool")
        if required_tools is None:
            required_tools = []
            required_scanning["required_code_scanning_tool"] = required_tools
        if not isinstance(required_tools, list):
            raise TypeError("required_code_scanning_tool must be a list")

        for tool in [CODEQL_REQUIRED_TOOL] + (
            [TRIVY_REQUIRED_TOOL] if require_trivy else []
        ):
            if not any(
                isinstance(existing, dict) and existing.get("tool") == tool["tool"]
                for existing in required_tools
            ):
                required_tools.append(copy.deepcopy(tool))

        if require_sonarcloud:
            required_status_checks = rules.get("required_status_checks")
            if required_status_checks is None:
                required_status_checks = {}
                rules["required_status_checks"] = required_status_checks
            if not isinstance(required_status_checks, dict):
                raise TypeError("required_status_checks must be a mapping")

            required_checks = required_status_checks.get("required_check")
            if required_checks is None:
                required_checks = []
                required_status_checks["required_check"] = required_checks
            if not isinstance(required_checks, list):
                raise TypeError("required_status_checks.required_check must be a list")

            if not any(
                isinstance(check, dict)
                and check.get("context") == SONARCLOUD_REQUIRED_CHECK
                for check in required_checks
            ):
                required_checks.append({"context": SONARCLOUD_REQUIRED_CHECK})

    return rulesets


def normalize_conditions(conditions: dict | None) -> dict | None:
    """Fill ref_name defaults, or return None when no ref_name is declared."""
    ref_name = (conditions or {}).get("ref_name")
    if ref_name is None:
        return None
    return {
        "ref_name": {
            "include": ref_name.get("include", ["~DEFAULT_BRANCH"]),
            "exclude": ref_name.get("exclude", []),
        }
    }


RULE_BLOCK_DEFAULTS = {
    "pull_request": RULESET_PULL_REQUEST_DEFAULTS,
    "required_status_checks": RULESET_REQUIRED_STATUS_CHECKS_DEFAULTS,
    "required_code_scanning": RULESET_REQUIRED_CODE_SCANNING_DEFAULTS,
    "copilot_code_review": RULESET_COPILOT_CODE_REVIEW_DEFAULTS,
}


def normalize_rules(rules: dict | None) -> dict | None:
    """Fill rule defaults, including those of each declared rule block."""
    if rules is None:
        return None
    rules = merge_defaults(rules, RULESET_DEFAULTS["rules"])
    for block, defaults in RULE_BLOCK_DEFAULTS.items():
        if rules.get(block) is not None:
            rules[block] = merge_defaults(rules[block], defaults)
    return rules


def parse_rulesets(rulesets_data: list[dict] | None) -> list[dict]:
    """Normalize repository rulesets with nested defaults."""
    normalized: list[dict] = []
    for ruleset_data in rulesets_data or []:
        ruleset = merge_defaults(ruleset_data, RULESET_DEFAULTS)
        ruleset["conditions"] = normalize_conditions(ruleset.get("conditions"))
        ruleset["rules"] = normalize_rules(ruleset.get("rules"))
        normalized.append(ruleset)
    return normalized


def load_repo_config(file_path: Path) -> tuple[str, dict]:
    """Load and validate a single repository YAML config file.

    Returns a (repo_name, config_dict) tuple.
    """
    with file_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise TypeError(
            f"Expected a YAML mapping in {file_path}, got {type(raw).__name__}"
        )

    # Use 'name' from YAML if present, otherwise derive from filename
    repo_name: str = raw.get("name") or file_path.stem

    config = merge_defaults(raw, SCHEMA_DEFAULTS)
    config["rulesets"] = parse_rulesets(
        with_default_rulesets(raw.get("rulesets"), config.get("code_scanning"))
    )

    # Remove 'name' key from the config value – it is used as the map key
    config.pop("name", None)
    # These options are consumed to construct ruleset rules, not Terraform inputs.
    config.pop("code_scanning", None)

    return repo_name, config


def load_all_configs(config_dir: Path) -> dict:
    """Load all YAML files from config_dir and return a repositories map."""
    repositories: dict[str, dict] = {}

    all_yaml_files = sorted(config_dir.glob("*.yaml")) + sorted(
        config_dir.glob("*.yml")
    )
    skipped_example_files = [f for f in all_yaml_files if f.name.startswith("example")]
    yaml_files = [f for f in all_yaml_files if not f.name.startswith("example")]

    for skipped in skipped_example_files:
        print(
            f"Warning: skipping example config file '{skipped.as_posix()}'.",
            file=sys.stderr,
        )

    if not yaml_files:
        print(f"Warning: no YAML files found in {config_dir}", file=sys.stderr)

    for yaml_file in yaml_files:
        try:
            repo_name, config = load_repo_config(yaml_file)
        except (OSError, ValueError, TypeError, yaml.YAMLError) as exc:
            print(f"Error loading {yaml_file}: {exc}", file=sys.stderr)
            sys.exit(1)

        if repo_name in repositories:
            print(
                f"Warning: duplicate repository name '{repo_name}' from {yaml_file}. Skipping.",
                file=sys.stderr,
            )
            continue

        repositories[repo_name] = config

    return repositories


def format_hcl_key(key: str) -> str:
    """Render an HCL object key, quoting when required."""
    if HCL_IDENTIFIER_RE.match(key):
        return key
    return json.dumps(key, ensure_ascii=False)


def to_hcl(value, indent: int = 0) -> str:
    """Serialize Python data structures into HCL literals."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        if not value:
            return "[]"
        item_indent = " " * (indent + 2)
        closing_indent = " " * indent
        rendered_items = [f"{item_indent}{to_hcl(item, indent + 2)}," for item in value]
        return "[\n" + "\n".join(rendered_items) + f"\n{closing_indent}]"
    if isinstance(value, dict):
        if not value:
            return "{}"
        item_indent = " " * (indent + 2)
        closing_indent = " " * indent
        lines = ["{"]
        for key, item in value.items():
            rendered_key = format_hcl_key(str(key))
            rendered_value = to_hcl(item, indent + 2)
            lines.append(f"{item_indent}{rendered_key} = {rendered_value}")
        lines.append(f"{closing_indent}}}")
        return "\n".join(lines)

    raise TypeError(
        f"Unsupported value type for HCL serialization: {type(value).__name__}"
    )


def resolve_in_workspace(path: Path) -> Path:
    """Resolve a path and ensure it stays inside the current working directory."""
    resolved = path.resolve()
    if not resolved.is_relative_to(Path.cwd().resolve()):
        print(f"Error: '{path}' is outside the working directory.", file=sys.stderr)
        sys.exit(1)
    return resolved


def write_tfvars(repositories: dict, output_path: Path) -> None:
    """Write the repositories map as an HCL .auto.tfvars file."""
    payload = f"repositories = {to_hcl(repositories)}\n"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(payload)
    print(f"Generated: {output_path} ({len(repositories)} repositories)")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a Terraform tfvars file from YAML repository configs."
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Directory containing YAML repository config files (default: config)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("src/repositories.auto.tfvars"),
        help="Output tfvars HCL file path (default: src/repositories.auto.tfvars)",
    )
    args = parser.parse_args()

    config_dir: Path = resolve_in_workspace(args.config_dir)
    output_path: Path = resolve_in_workspace(args.output)

    if not config_dir.is_dir():
        print(
            f"Error: config directory '{config_dir}' does not exist.", file=sys.stderr
        )
        sys.exit(1)

    repositories = load_all_configs(config_dir)
    write_tfvars(repositories, output_path)


if __name__ == "__main__":
    main()
