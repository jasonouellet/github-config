# Unit tests for the IaC github_repository module.
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
# Test: public repository with ruleset
# ---------------------------------------------------------------------------
run "full_repository" {
  command = plan

  variables {
    name        = "test-repo-full"
    description = "A fully configured test repository."
    visibility  = "public"
    topics      = ["terraform", "test"]
    rulesets = [{
      name        = "main"
      target      = "branch"
      enforcement = "active"
      conditions = {
        ref_name = {
          include = ["~DEFAULT_BRANCH"]
          exclude = []
        }
      }
      rules = {
        required_signatures = true
        pull_request = {
          required_approving_review_count   = 1
          dismiss_stale_reviews_on_push     = true
          require_code_owner_review         = false
          require_last_push_approval        = false
          required_review_thread_resolution = false
          allowed_merge_methods             = ["merge", "squash", "rebase"]
        }
      }
    }]
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
