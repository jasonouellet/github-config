output "name" {
  description = "The name of the repository."
  value       = github_repository.this.name
}

output "full_name" {
  description = "The full name of the repository (owner/name)."
  value       = github_repository.this.full_name
}

output "html_url" {
  description = "The URL to the repository on GitHub."
  value       = github_repository.this.html_url
}

output "ssh_clone_url" {
  description = "The SSH clone URL of the repository."
  value       = github_repository.this.ssh_clone_url
}

output "http_clone_url" {
  description = "The HTTPS clone URL of the repository."
  value       = github_repository.this.http_clone_url
}

output "node_id" {
  description = "The Node ID of the repository."
  value       = github_repository.this.node_id
}

output "repo_id" {
  description = "The GitHub repository ID."
  value       = github_repository.this.repo_id
}
