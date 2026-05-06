resource "github_repository" "this" {
  name                   = var.name
  description            = var.description
  visibility             = var.visibility
  has_issues             = true
  has_projects           = false
  has_wiki               = false
  is_template            = var.is_template
  delete_branch_on_merge = true
  auto_init              = var.auto_init
  gitignore_template     = var.gitignore_template
  license_template       = var.license_template
  topics                 = var.topics
  archived               = var.archived
}

resource "github_repository_vulnerability_alerts" "this" {
  repository = github_repository.this.name
  enabled    = true
}

resource "github_branch_protection" "this" {
  count = var.branch_protection != null ? 1 : 0

  repository_id = github_repository.this.node_id
  pattern       = var.branch_protection.pattern

  enforce_admins         = var.branch_protection.enforce_admins
  require_signed_commits = var.branch_protection.require_signed_commits

  dynamic "required_status_checks" {
    for_each = var.branch_protection.required_status_checks != null ? [var.branch_protection.required_status_checks] : []
    content {
      strict   = required_status_checks.value.strict
      contexts = required_status_checks.value.contexts
    }
  }

  dynamic "required_pull_request_reviews" {
    for_each = var.branch_protection.required_pull_request_reviews != null ? [var.branch_protection.required_pull_request_reviews] : []
    content {
      dismiss_stale_reviews           = required_pull_request_reviews.value.dismiss_stale_reviews
      require_code_owner_reviews      = required_pull_request_reviews.value.require_code_owner_reviews
      required_approving_review_count = required_pull_request_reviews.value.required_approving_review_count
    }
  }
}
