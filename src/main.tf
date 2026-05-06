module "repositories" {
  for_each = var.repositories
  source   = "./modules/github_repository"

  name                   = each.key
  description            = each.value.description
  visibility             = each.value.visibility
  has_issues             = each.value.has_issues
  has_projects           = each.value.has_projects
  has_wiki               = each.value.has_wiki
  is_template            = each.value.is_template
  delete_branch_on_merge = each.value.delete_branch_on_merge
  auto_init              = each.value.auto_init
  gitignore_template     = each.value.gitignore_template
  license_template       = each.value.license_template
  topics                 = each.value.topics
  archived               = each.value.archived
  vulnerability_alerts   = each.value.vulnerability_alerts
  branch_protection      = each.value.branch_protection
}
