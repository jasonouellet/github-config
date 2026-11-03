terraform {
  backend "remote" {
    hostname     = "app.terraform.io"
    organization = "jasonouellet"
    workspaces {
      name = "github-config"
    }
  }
}
