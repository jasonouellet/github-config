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
    "import_id": None,
    "rulesets": [],
}

RULESET_DEFAULTS = {
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

HCL_IDENTIFIER_RE = re.compile(r"^[A-Za-z_]\w*$")


def merge_defaults(data: dict, defaults: dict) -> dict:
    """Return a new dict that is defaults overridden by data."""
    result = {**defaults}
    for key, value in data.items():
        if key in result:
            result[key] = value
    return result


def parse_rulesets(rulesets_data: list[dict] | None) -> list[dict]:
    """Normalize repository rulesets with nested defaults."""
    if not rulesets_data:
        return []

    normalized: list[dict] = []
    for ruleset_data in rulesets_data:
        ruleset = merge_defaults(ruleset_data, RULESET_DEFAULTS)

        conditions = ruleset.get("conditions")
        if conditions is None:
            ruleset["conditions"] = None
        else:
            ref_name = conditions.get("ref_name")
            if ref_name is None:
                ruleset["conditions"] = None
            else:
                ruleset["conditions"] = {
                    "ref_name": {
                        "include": ref_name.get("include", ["~DEFAULT_BRANCH"]),
                        "exclude": ref_name.get("exclude", []),
                    }
                }

        rules = ruleset.get("rules")
        if rules is None:
            ruleset["rules"] = None
        else:
            rules = merge_defaults(rules, RULESET_DEFAULTS["rules"])

            if rules.get("pull_request") is not None:
                rules["pull_request"] = merge_defaults(
                    rules["pull_request"], RULESET_PULL_REQUEST_DEFAULTS
                )

            if rules.get("required_status_checks") is not None:
                rules["required_status_checks"] = merge_defaults(
                    rules["required_status_checks"],
                    RULESET_REQUIRED_STATUS_CHECKS_DEFAULTS,
                )

            if rules.get("required_code_scanning") is not None:
                rules["required_code_scanning"] = merge_defaults(
                    rules["required_code_scanning"],
                    RULESET_REQUIRED_CODE_SCANNING_DEFAULTS,
                )

            if rules.get("copilot_code_review") is not None:
                rules["copilot_code_review"] = merge_defaults(
                    rules["copilot_code_review"],
                    RULESET_COPILOT_CODE_REVIEW_DEFAULTS,
                )

            ruleset["rules"] = rules

        normalized.append(ruleset)

    return normalized


def load_repo_config(file_path: Path) -> tuple[str, dict]:
    """Load and validate a single repository YAML config file.

    Returns a (repo_name, config_dict) tuple.
    """
    with file_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(
            f"Expected a YAML mapping in {file_path}, got {type(raw).__name__}"
        )

    # Use 'name' from YAML if present, otherwise derive from filename
    repo_name: str = raw.get("name") or file_path.stem

    config = merge_defaults(raw, SCHEMA_DEFAULTS)
    config["rulesets"] = parse_rulesets(raw.get("rulesets"))

    # Remove 'name' key from the config value – it is used as the map key
    config.pop("name", None)

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
        except Exception as exc:
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

    config_dir: Path = args.config_dir
    output_path: Path = args.output

    if not config_dir.is_dir():
        print(
            f"Error: config directory '{config_dir}' does not exist.", file=sys.stderr
        )
        sys.exit(1)

    repositories = load_all_configs(config_dir)
    write_tfvars(repositories, output_path)


if __name__ == "__main__":
    main()
