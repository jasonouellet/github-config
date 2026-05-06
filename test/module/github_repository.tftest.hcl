# Unit tests for the github_repository module.
# Run from the test/module/ directory:
#   tofu init && tofu test
#
# Uses a mock provider so no real GitHub API calls are made.

mock_provider "github" {}

# ---------------------------------------------------------------------------
# Test: minimal configuration (only required input)
# ---------------------------------------------------------------------------
run "minimal_repository" {
  command = plan

  variables {
    name = "test-repo-minimal"
  }

  assert {
    condition     = module.under_test.name == "test-repo-minimal"
    error_message = "Repository name must match the input variable."
  }
}

# ---------------------------------------------------------------------------
# Test: public repository with branch protection
# ---------------------------------------------------------------------------
run "full_repository" {
  command = plan

  variables {
    name        = "test-repo-full"
    description = "A fully configured test repository."
    visibility  = "public"
    topics      = ["terraform", "test"]
    branch_protection = {
      pattern                = "main"
      enforce_admins         = false
      require_signed_commits = true
      required_status_checks = {
        strict   = true
        contexts = ["ci/test"]
      }
      required_pull_request_reviews = {
        dismiss_stale_reviews           = true
        require_code_owner_reviews      = false
        required_approving_review_count = 1
      }
    }
  }

  assert {
    condition     = module.under_test.name == "test-repo-full"
    error_message = "Repository name must be 'test-repo-full'."
  }
}

# ---------------------------------------------------------------------------
# Test: archived repository
# ---------------------------------------------------------------------------
run "archived_repository" {
  command = plan

  variables {
    name     = "test-repo-archived"
    archived = true
  }

  assert {
    condition     = module.under_test.name == "test-repo-archived"
    error_message = "Repository name must be 'test-repo-archived'."
  }
}
