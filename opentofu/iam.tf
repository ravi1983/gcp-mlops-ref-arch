resource "google_service_account" "mlops_sa" {
  account_id = "mlops-service-account"
  display_name = "MLOps Service Reader"
  description = "Service account for MLOps"
  project = var.PROJECT_ID
}

resource "google_project_iam_member" "mlops_roles" {
  for_each = toset([
    "roles/aiplatform.user",
    "roles/bigquery.dataEditor",
    "roles/storage.objectViewer",
    "roles/bigquery.admin"
  ])

  project = var.PROJECT_ID
  role = each.key
  member = "serviceAccount:${google_service_account.mlops_sa.email}"
}