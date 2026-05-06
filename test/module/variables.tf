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

variable "branch_protection" {
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
