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
  has_projects           = each.value.has_projects
  has_wiki               = each.value.has_wiki
  delete_branch_on_merge = each.value.delete_branch_on_merge
  has_issues             = each.value.has_issues
  allow_merge_commit     = each.value.allow_merge_commit
  allow_rebase_merge     = each.value.allow_rebase_merge

  merge_commit_title          = each.value.merge_commit_title
  merge_commit_message        = each.value.merge_commit_message
  squash_merge_commit_title   = each.value.squash_merge_commit_title
  squash_merge_commit_message = each.value.squash_merge_commit_message

  rulesets = each.value.rulesets
}
