module "repositories" {
  for_each = var.repositories
  source   = "./modules/github_repository"

  name                   = each.key
  description            = each.value.description
  visibility             = each.value.visibility
  is_template            = each.value.is_template
  auto_init              = each.value.auto_init
  gitignore_template     = each.value.gitignore_template
  license_template       = each.value.license_template
  topics                 = each.value.topics
  archived               = each.value.archived
  branch_protection      = each.value.branch_protection
}
