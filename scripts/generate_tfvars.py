#!/usr/bin/env python3
"""
generate_tfvars.py

Reads all YAML files from the config/ directory and generates a
repositories.auto.tfvars.json file consumed by Terraform in src/.

Usage:
    python scripts/generate_tfvars.py [--config-dir CONFIG_DIR] [--output OUTPUT]

Options:
    --config-dir    Directory containing YAML repository config files
                    (default: config)
    --output        Path for the generated tfvars JSON file
                    (default: src/repositories.auto.tfvars.json)
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Error: PyYAML is required. Install it with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


SCHEMA_DEFAULTS = {
    "description": "",
    "visibility": "private",
    "has_issues": True,
    "has_projects": False,
    "has_wiki": False,
    "is_template": False,
    "delete_branch_on_merge": True,
    "auto_init": True,
    "gitignore_template": None,
    "license_template": None,
    "topics": [],
    "archived": False,
    "vulnerability_alerts": True,
    "branch_protection": None,
}

BRANCH_PROTECTION_DEFAULTS = {
    "pattern": "main",
    "enforce_admins": False,
    "require_signed_commits": False,
    "required_status_checks": None,
    "required_pull_request_reviews": None,
}

REQUIRED_STATUS_CHECKS_DEFAULTS = {
    "strict": True,
    "contexts": [],
}

REQUIRED_PR_REVIEWS_DEFAULTS = {
    "dismiss_stale_reviews": True,
    "require_code_owner_reviews": False,
    "required_approving_review_count": 1,
}


def merge_defaults(data: dict, defaults: dict) -> dict:
    """Return a new dict that is defaults overridden by data."""
    result = {**defaults}
    for key, value in data.items():
        if key in result:
            result[key] = value
    return result


def parse_branch_protection(bp_data: dict) -> dict | None:
    """Normalize branch_protection block with nested defaults."""
    if bp_data is None:
        return None

    bp = merge_defaults(bp_data, BRANCH_PROTECTION_DEFAULTS)

    if bp.get("required_status_checks") is not None:
        bp["required_status_checks"] = merge_defaults(
            bp["required_status_checks"], REQUIRED_STATUS_CHECKS_DEFAULTS
        )

    if bp.get("required_pull_request_reviews") is not None:
        bp["required_pull_request_reviews"] = merge_defaults(
            bp["required_pull_request_reviews"], REQUIRED_PR_REVIEWS_DEFAULTS
        )

    return bp


def load_repo_config(file_path: Path) -> tuple[str, dict]:
    """Load and validate a single repository YAML config file.

    Returns a (repo_name, config_dict) tuple.
    """
    with file_path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping in {file_path}, got {type(raw).__name__}")

    # Use 'name' from YAML if present, otherwise derive from filename
    repo_name: str = raw.get("name") or file_path.stem

    config = merge_defaults(raw, SCHEMA_DEFAULTS)
    config["branch_protection"] = parse_branch_protection(raw.get("branch_protection"))

    # Remove 'name' key from the config value – it is used as the map key
    config.pop("name", None)

    return repo_name, config


def load_all_configs(config_dir: Path) -> dict:
    """Load all YAML files from config_dir and return a repositories map."""
    repositories: dict[str, dict] = {}

    yaml_files = sorted(config_dir.glob("*.yaml")) + sorted(config_dir.glob("*.yml"))
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


def write_tfvars(repositories: dict, output_path: Path) -> None:
    """Write the repositories map as a .tfvars.json file."""
    payload = {"repositories": repositories}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
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
        default=Path("src/repositories.auto.tfvars.json"),
        help="Output tfvars JSON file path (default: src/repositories.auto.tfvars.json)",
    )
    args = parser.parse_args()

    config_dir: Path = args.config_dir
    output_path: Path = args.output

    if not config_dir.is_dir():
        print(f"Error: config directory '{config_dir}' does not exist.", file=sys.stderr)
        sys.exit(1)

    repositories = load_all_configs(config_dir)
    write_tfvars(repositories, output_path)


if __name__ == "__main__":
    main()
