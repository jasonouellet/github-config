locals {
  import_repos = {
    for name, config in var.repositories :
    name => config
    if config.import_id == true
  }

  import_rulesets = {
    for item in flatten([
      for repo_name, config in local.import_repos : [
        for ruleset in try(config.rulesets, []) : {
          key       = "${repo_name}:${ruleset.name}"
          repo_name = repo_name
          ruleset   = ruleset
        }
      ]
    ]) :
    item.key => item
    if try(item.ruleset.import_id, null) != null
  }
}

import {
  for_each = local.import_repos

  to = module.repositories[each.key].github_repository.this
  id = each.key
}

import {
  for_each = local.import_repos

  to = module.repositories[each.key].github_repository_vulnerability_alerts.this
  id = each.key
}

import {
  for_each = local.import_rulesets

  to = module.repositories[each.value.repo_name].github_repository_ruleset.this[each.value.ruleset.name]
  id = "${each.value.repo_name}:${each.value.ruleset.import_id}"
}
