output "repository_names" {
  description = "Names of all managed repositories."
  value       = { for k, v in module.repositories : k => v.name }
}

output "repository_urls" {
  description = "HTML URLs of all managed repositories."
  value       = { for k, v in module.repositories : k => v.html_url }
}

output "repository_http_clone_urls" {
  description = "HTTPS clone URLs of all managed repositories."
  value       = { for k, v in module.repositories : k => v.http_clone_url }
}
