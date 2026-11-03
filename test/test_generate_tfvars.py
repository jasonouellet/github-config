import tempfile
import unittest
from pathlib import Path

from scripts.generate_tfvars import load_repo_config


class CodeScanningDefaultsTest(unittest.TestCase):
    def load_config(self, content: str) -> dict:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "repository.yaml"
            config_path.write_text(content, encoding="utf-8")
            _, config = load_repo_config(config_path)
        return config

    def required_tool_names(self, config: dict) -> set[str]:
        rules = config["rulesets"][0]["rules"]
        return {
            entry["tool"]
            for entry in rules["required_code_scanning"]["required_code_scanning_tool"]
        }

    def test_codeql_is_required_by_default(self) -> None:
        config = self.load_config("name: example\n")

        self.assertEqual(self.required_tool_names(config), {"CodeQL"})
        self.assertNotIn("code_scanning", config)

    def test_sonarcloud_option_requires_published_status_check(self) -> None:
        config = self.load_config(
            "name: example\ncode_scanning:\n  require_sonarcloud: true\n"
        )
        rules = config["rulesets"][0]["rules"]

        self.assertEqual(self.required_tool_names(config), {"CodeQL"})
        self.assertIn(
            {"context": "SonarCloud Code Analysis"},
            rules["required_status_checks"]["required_check"],
        )

    def test_trivy_option_adds_code_scanning_tool(self) -> None:
        config = self.load_config(
            "name: example\ncode_scanning:\n  require_trivy: true\n"
        )

        self.assertEqual(self.required_tool_names(config), {"CodeQL", "Trivy"})

    def test_custom_main_ruleset_cannot_remove_codeql(self) -> None:
        config = self.load_config(
            """\
name: example
rulesets:
  - name: main
    rules:
      required_code_scanning:
        required_code_scanning_tool:
          - tool: Trivy
            security_alerts_threshold: high_or_higher
            alerts_threshold: errors
"""
        )

        self.assertEqual(self.required_tool_names(config), {"CodeQL", "Trivy"})

    def test_optional_scanner_requires_a_main_ruleset(self) -> None:
        with self.assertRaisesRegex(ValueError, "require a 'main' ruleset"):
            self.load_config(
                "name: example\nrulesets: []\ncode_scanning:\n  require_trivy: true\n"
            )


if __name__ == "__main__":
    unittest.main()
