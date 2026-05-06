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
    import_id              = optional(bool, null)
    branch_protection = optional(object({
      pattern                = optional(string, "main")
      enforce_admins         = optional(bool, false)
      require_signed_commits = optional(bool, false)
      required_status_checks = optional(object({
        strict   = optional(bool, true)
        contexts = optional(list(string), [])
      }), null)
      required_pull_request_reviews = optional(object({
        dismiss_stale_reviews           = optional(bool, true)
        require_code_owner_reviews      = optional(bool, false)
        required_approving_review_count = optional(number, 1)
      }), null)
    }), null)
  }))
  default = {}
}
