resource "google_project" "vertex-mlops" {
  name            = "vertex-mlops"
  project_id      = "vertex-mlops-2"
  billing_account = var.BILLING_ACCOUNT
}

output "project_id" {
  value = google_project.vertex-mlops.id
}