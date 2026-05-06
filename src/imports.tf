locals {
  import_repos = {
    for name, config in var.repositories :
    name => config
    if config.import_id != null
  }
}

import {
  for_each = local.import_repos

  to = module.repositories[each.key].github_repository.this
  id = "${var.github_owner}/${each.key}"
}
