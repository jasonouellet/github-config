# Integration tests for the IaC root module (src/).
# Run from the src/ directory:
#   tofu init -backend=false && tofu test
#
# Uses a mock provider so no real GitHub API calls are made.

mock_provider "github" {}

# ---------------------------------------------------------------------------
# Test: root module iterates over all repositories in the variable map
# ---------------------------------------------------------------------------
run "multiple_repositories" {
  command = plan

  variables {
    github_token = "mock-token"
    github_owner = "mock-org"
    repositories = {
      "repo-alpha" = {
        description = "First test repository."
        visibility  = "public"
        topics      = ["alpha"]
      }
      "repo-beta" = {
        description = "Second test repository."
        visibility  = "private"
      }
    }
  }

  assert {
    condition     = length(module.repositories) == 2
    error_message = "Root module must create one module instance per repository entry."
  }

  assert {
    condition     = module.repositories["repo-alpha"].name == "repo-alpha"
    error_message = "Module for 'repo-alpha' must use the map key as its name."
  }

  assert {
    condition     = module.repositories["repo-beta"].name == "repo-beta"
    error_message = "Module for 'repo-beta' must use the map key as its name."
  }
}

# ---------------------------------------------------------------------------
# Test: empty repositories map produces no resources
# ---------------------------------------------------------------------------
run "empty_repositories" {
  command = plan

  variables {
    github_token = "mock-token"
    github_owner = "mock-org"
    repositories = {}
  }

  assert {
    condition     = length(module.repositories) == 0
    error_message = "No module instances should be created when repositories map is empty."
  }
}
