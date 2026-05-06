terraform {
  required_version = ">= 1.6.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# Provider is mocked in .tftest.hcl files; no real credentials needed for tests.
provider "github" {
  token = "mock"
  owner = "mock-org"
}

module "under_test" {
  source = "../../src/modules/github_repository"

  name              = var.name
  description       = var.description
  visibility        = var.visibility
  is_template       = var.is_template
  auto_init         = var.auto_init
  gitignore_template = var.gitignore_template
  license_template  = var.license_template
  topics            = var.topics
  archived          = var.archived
  branch_protection = var.branch_protection
}
