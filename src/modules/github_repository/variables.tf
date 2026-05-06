variable "name" {
  description = "The name of the repository."
  type        = string
}

variable "description" {
  description = "A short description of the repository."
  type        = string
  default     = ""
}

variable "visibility" {
  description = "Repository visibility: public, private, or internal."
  type        = string
  default     = "private"

  validation {
    condition     = contains(["public", "private", "internal"], var.visibility)
    error_message = "visibility must be one of: public, private, internal."
  }
}

variable "has_issues" {
  description = "Enable GitHub Issues for the repository."
  type        = bool
  default     = true
}

variable "has_projects" {
  description = "Enable GitHub Projects for the repository."
  type        = bool
  default     = false
}

variable "has_wiki" {
  description = "Enable GitHub Wiki for the repository."
  type        = bool
  default     = false
}

variable "is_template" {
  description = "Mark the repository as a template repository."
  type        = bool
  default     = false
}

variable "delete_branch_on_merge" {
  description = "Automatically delete head branches when pull requests are merged."
  type        = bool
  default     = true
}

variable "auto_init" {
  description = "Initialize the repository with a README."
  type        = bool
  default     = true
}

variable "gitignore_template" {
  description = "Use a .gitignore template for the repository (e.g. \"Terraform\")."
  type        = string
  default     = null
}

variable "license_template" {
  description = "Use a license template for the repository (e.g. \"mit\")."
  type        = string
  default     = null
}

variable "topics" {
  description = "List of topics to apply to the repository."
  type        = list(string)
  default     = []
}

variable "archived" {
  description = "Archive the repository, making it read-only."
  type        = bool
  default     = false
}

variable "vulnerability_alerts" {
  description = "Enable Dependabot vulnerability alerts on the repository."
  type        = bool
  default     = true
}

variable "branch_protection" {
  description = "Branch protection rule configuration. Set to null to skip."
  type = object({
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
  })
  default = null
}
