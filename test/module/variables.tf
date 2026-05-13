variable "name" {
  type = string
}

variable "description" {
  type    = string
  default = ""
}

variable "visibility" {
  type    = string
  default = "private"
}

variable "is_template" {
  type    = bool
  default = false
}

variable "auto_init" {
  type    = bool
  default = true
}

variable "gitignore_template" {
  type    = string
  default = null
}

variable "license_template" {
  type    = string
  default = null
}

variable "topics" {
  type    = list(string)
  default = []
}

variable "archived" {
  type    = bool
  default = false
}

variable "rulesets" {
  type = list(object({
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
  }))
  default = []
}
