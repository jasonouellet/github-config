variable "github_token" {
  description = "GitHub personal access token with repository management permissions."
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub organization or user name that owns the repositories."
  type        = string
}

variable "repositories" {
  description = "Map of repository configurations keyed by repository name."
  type = map(object({
    description            = optional(string, "")
    visibility             = optional(string, "private")
    is_template            = optional(bool, false)
    auto_init              = optional(bool, true)
    gitignore_template     = optional(string, null)
    license_template       = optional(string, null)
    topics                 = optional(list(string), [])
    archived               = optional(bool, false)
    has_projects           = optional(bool, false)
    has_wiki               = optional(bool, false)
    delete_branch_on_merge = optional(bool, true)
    import_id              = optional(bool, false)
    rulesets = optional(list(object({
      name        = string
      target      = optional(string, "branch")
      enforcement = optional(string, "active")
      import_id   = optional(number, null)
      bypass_actors = optional(list(object({
        actor_id    = optional(number)
        actor_type  = string
        bypass_mode = string
      })), [])
      conditions = optional(object({
        ref_name = object({
          include = optional(list(string), ["~DEFAULT_BRANCH"])
          exclude = optional(list(string), [])
        })
      }), null)
      rules = object({
        creation                      = optional(bool)
        update                        = optional(bool)
        deletion                      = optional(bool)
        required_linear_history       = optional(bool)
        required_signatures           = optional(bool)
        non_fast_forward              = optional(bool)
        update_allows_fetch_and_merge = optional(bool)
        pull_request = optional(object({
          dismiss_stale_reviews_on_push     = optional(bool, false)
          require_code_owner_review         = optional(bool, false)
          require_last_push_approval        = optional(bool, false)
          required_approving_review_count   = optional(number, 0)
          required_review_thread_resolution = optional(bool, false)
          allowed_merge_methods             = optional(list(string), ["merge", "squash", "rebase"])
          required_reviewers = optional(list(object({
            file_patterns     = list(string)
            minimum_approvals = number
            reviewer = object({
              id   = number
              type = string
            })
          })), [])
        }), null)
        required_status_checks = optional(object({
          strict_required_status_checks_policy = optional(bool, true)
          do_not_enforce_on_create             = optional(bool, false)
          required_check = optional(list(object({
            context        = string
            integration_id = optional(number)
          })), [])
        }), null)
        required_code_scanning = optional(object({
          required_code_scanning_tool = list(object({
            tool                      = string
            alerts_threshold          = string
            security_alerts_threshold = string
          }))
        }), null)
        copilot_code_review = optional(object({
          review_on_push             = optional(bool, false)
          review_draft_pull_requests = optional(bool, false)
        }), null)
      })
    })), [])
  }))
  default = {}
}
