#!/usr/bin/env python3
"""
validate_config.py

Validates YAML repository config files in config/ against a JSON Schema
and optionally writes a Sonar-compatible generic issue report.

Usage:
    python scripts/validate_config.py [options]

Options:
    --config-dir DIR    Directory with YAML config files (default: config)
    --schema FILE       Path to JSON Schema file
                        (default: schemas/repository.schema.json)
    --report FILE       Write a Sonar-compatible generic issue report to FILE

Exit codes:
    0  All files passed validation
    1  One or more files failed validation or an error occurred
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print(
        "Error: PyYAML is required. Install with: pip install pyyaml", file=sys.stderr
    )
    sys.exit(1)

try:
    from jsonschema import Draft7Validator, SchemaError
except ImportError:
    print(
        "Error: jsonschema is required. Install with: pip install jsonschema",
        file=sys.stderr,
    )
    sys.exit(1)


def load_schema(schema_path: Path) -> dict:
    """Load and return the JSON Schema from schema_path."""
    with schema_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def validate_file(file_path: Path, validator: Draft7Validator) -> list[str]:
    """Validate a single YAML config file. Returns a list of error messages."""
    errors: list[str] = []
    try:
        with file_path.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
    except yaml.YAMLError as exc:
        errors.append(f"YAML parse error: {exc}")
        return errors

    if data is None:
        errors.append("File is empty or contains only whitespace.")
        return errors

    for error in sorted(validator.iter_errors(data), key=lambda e: tuple(e.path)):
        path = ".".join(str(p) for p in error.path) if error.path else "<root>"
        errors.append(f"{path}: {error.message}")

    return errors


def validate_all(config_dir: Path, validator: Draft7Validator) -> dict[str, list[str]]:
    """
    Validate all YAML files in config_dir.

    Returns {relative_path: [errors]}, using paths relative to the current
    working directory when possible for Sonar compatibility, and otherwise
    falling back to paths relative to config_dir.
    """
    results: dict[str, list[str]] = {}

    yaml_files = sorted(config_dir.glob("*.yaml")) + sorted(config_dir.glob("*.yml"))
    if not yaml_files:
        print(f"Warning: no YAML files found in {config_dir}", file=sys.stderr)

    cwd = Path.cwd().resolve()
    resolved_config_dir = config_dir.resolve()

    for yaml_file in yaml_files:
        resolved_yaml_file = yaml_file.resolve()
        try:
            relative = resolved_yaml_file.relative_to(cwd).as_posix()
        except ValueError:
            relative = resolved_yaml_file.relative_to(resolved_config_dir).as_posix()
        results[relative] = validate_file(yaml_file, validator)

    return results


def build_sonar_report(results: dict[str, list[str]]) -> dict:
    """Build a Sonar-compatible generic issue report dict."""
    issues = []
    for file_path, errors in results.items():
        for error in errors:
            issues.append(
                {
                    "engineId": "yaml-schema-validator",
                    "ruleId": "repository-config-schema",
                    "severity": "MAJOR",
                    "type": "BUG",
                    "primaryLocation": {
                        "message": error,
                        "filePath": file_path,
                    },
                }
            )
    return {"issues": issues}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate YAML repository config files against a JSON Schema."
    )
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("config"),
        help="Directory containing YAML repository config files (default: config)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("schemas/repository.schema.json"),
        help="Path to the JSON Schema file (default: schemas/repository.schema.json)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=None,
        metavar="FILE",
        help="Write a Sonar-compatible generic issue report to FILE",
    )
    args = parser.parse_args()

    if not args.config_dir.is_dir():
        print(
            f"Error: config directory '{args.config_dir}' does not exist.",
            file=sys.stderr,
        )
        sys.exit(1)

    if not args.schema.is_file():
        print(
            f"Error: schema file '{args.schema}' does not exist.",
            file=sys.stderr,
        )
        sys.exit(1)

    schema = load_schema(args.schema)
    try:
        Draft7Validator.check_schema(schema)
    except SchemaError as exc:
        print(
            f"Error: invalid schema in '{args.schema}': {exc.message}", file=sys.stderr
        )
        sys.exit(1)

    validator = Draft7Validator(schema)
    results = validate_all(args.config_dir, validator)

    total = len(results)
    failed = sum(1 for errs in results.values() if errs)
    passed = total - failed

    for file_path, errors in results.items():
        status = "OK" if not errors else "FAIL"
        print(f"  [{status}] {file_path}")
        for error in errors:
            print(f"         - {error}")

    print(f"\nValidation: {passed}/{total} files passed.")

    if args.report is not None:
        report = build_sonar_report(results)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with args.report.open("w", encoding="utf-8") as fh:
            json.dump(report, fh, indent=2, ensure_ascii=False)
            fh.write("\n")
        print(f"Sonar report written to: {args.report}")

    if failed > 0:
        print(
            f"\nError: {failed} file(s) failed schema validation.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
