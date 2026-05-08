locals {
  import_repos = {
    for name, config in var.repositories :
    name => config
    if config.import_id == true
  }

  import_branch_protection_repos = {
    for name, config in local.import_repos :
    name => config
    if config.branch_protection != null
  }
}

import {
  for_each = local.import_repos

  to = module.repositories[each.key].github_repository.this
  id = each.key
}

import {
  for_each = local.import_branch_protection_repos

  to = module.repositories[each.key].github_branch_protection.this[0]
  id = "${each.key}:${each.value.branch_protection.pattern}"
}

import {
  for_each = local.import_repos

  to = module.repositories[each.key].github_repository_vulnerability_alerts.this
  id = each.key
}
