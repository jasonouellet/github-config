locals {
  import_repos = {
    for name, config in var.repositories :
    name => config
    if config.import_id != null
  }
}

import "github_repository" "repositories" {
  for_each = local.import_repos

  to = github_repository.this[each.key]
  id = "${var.github_owner}/${each.key}"
}
