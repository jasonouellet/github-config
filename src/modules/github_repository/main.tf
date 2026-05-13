resource "github_repository" "this" {
  name                   = var.name
  description            = var.description
  visibility             = var.visibility
  has_issues             = true
  has_projects           = var.has_projects
  has_wiki               = var.has_wiki
  is_template            = var.is_template
  delete_branch_on_merge = var.delete_branch_on_merge
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

locals {
  rulesets_by_name = {
    for rs in var.rulesets :
    rs.name => rs
  }
}

resource "github_repository_ruleset" "this" {
  for_each = local.rulesets_by_name

  repository  = github_repository.this.name
  name        = each.value.name
  target      = each.value.target
  enforcement = each.value.enforcement

  dynamic "bypass_actors" {
    for_each = each.value.bypass_actors
    content {
      actor_id    = try(bypass_actors.value.actor_id, null)
      actor_type  = bypass_actors.value.actor_type
      bypass_mode = bypass_actors.value.bypass_mode
    }
  }

  dynamic "conditions" {
    for_each = each.value.conditions != null ? [each.value.conditions] : []
    content {
      dynamic "ref_name" {
        for_each = [conditions.value.ref_name]
        content {
          include = ref_name.value.include
          exclude = ref_name.value.exclude
        }
      }
    }
  }

  rules {
    creation                      = each.value.rules.creation
    update                        = each.value.rules.update
    deletion                      = each.value.rules.deletion
    required_linear_history       = each.value.rules.required_linear_history
    required_signatures           = each.value.rules.required_signatures
    non_fast_forward              = each.value.rules.non_fast_forward
    update_allows_fetch_and_merge = each.value.rules.update_allows_fetch_and_merge

    dynamic "pull_request" {
      for_each = each.value.rules.pull_request != null ? [each.value.rules.pull_request] : []
      content {
        dismiss_stale_reviews_on_push     = pull_request.value.dismiss_stale_reviews_on_push
        require_code_owner_review         = pull_request.value.require_code_owner_review
        require_last_push_approval        = pull_request.value.require_last_push_approval
        required_approving_review_count   = pull_request.value.required_approving_review_count
        required_review_thread_resolution = pull_request.value.required_review_thread_resolution
        allowed_merge_methods             = pull_request.value.allowed_merge_methods

        dynamic "required_reviewers" {
          for_each = pull_request.value.required_reviewers
          content {
            file_patterns     = required_reviewers.value.file_patterns
            minimum_approvals = required_reviewers.value.minimum_approvals

            reviewer {
              id   = required_reviewers.value.reviewer.id
              type = required_reviewers.value.reviewer.type
            }
          }
        }
      }
    }

    dynamic "required_status_checks" {
      for_each = each.value.rules.required_status_checks != null ? [each.value.rules.required_status_checks] : []
      content {
        strict_required_status_checks_policy = required_status_checks.value.strict_required_status_checks_policy
        do_not_enforce_on_create             = required_status_checks.value.do_not_enforce_on_create

        dynamic "required_check" {
          for_each = required_status_checks.value.required_check
          content {
            context        = required_check.value.context
            integration_id = try(required_check.value.integration_id, null)
          }
        }
      }
    }

    dynamic "required_code_scanning" {
      for_each = each.value.rules.required_code_scanning != null ? [each.value.rules.required_code_scanning] : []
      content {
        dynamic "required_code_scanning_tool" {
          for_each = required_code_scanning.value.required_code_scanning_tool
          content {
            tool                      = required_code_scanning_tool.value.tool
            alerts_threshold          = required_code_scanning_tool.value.alerts_threshold
            security_alerts_threshold = required_code_scanning_tool.value.security_alerts_threshold
          }
        }
      }
    }

    dynamic "copilot_code_review" {
      for_each = each.value.rules.copilot_code_review != null ? [each.value.rules.copilot_code_review] : []
      content {
        review_on_push             = copilot_code_review.value.review_on_push
        review_draft_pull_requests = copilot_code_review.value.review_draft_pull_requests
      }
    }
  }
}
