terraform {
  required_version = ">= 1.6.0"

  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }

  backend "local" {}
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}
