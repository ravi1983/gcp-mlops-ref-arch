resource "google_storage_bucket" "ml_dataset" {
  name = "ml_dataset_gr8"
  location = var.REGION
  storage_class = "STANDARD"

  force_destroy = true
  uniform_bucket_level_access = true

  labels = {
    model = "cc-fraud"
  }
}

resource "google_storage_bucket" "pipeline_root" {
  name = "pipeline-artifacts-789y74"
  location = var.REGION
  storage_class = "STANDARD"

  force_destroy = true
  uniform_bucket_level_access = true

  labels = {
    model = "cc-fraud"
  }
}

resource "google_bigquery_dataset" "cc_fraud_dataset" {
  dataset_id = "cc_fraud_dataset"
  friendly_name = "CC Fraud Dataset"
  description = "Dataset for training model to predict CC fraud"
  location = var.REGION

  delete_contents_on_destroy = true
  default_table_expiration_ms = 432000000 # 5 days

  labels = {
    env = "production"
    model = "cc-fraud"
  }
}

resource "google_bigquery_table" "raw_cc_fraud_train" {
  dataset_id = google_bigquery_dataset.cc_fraud_dataset.dataset_id
  table_id = "raw_cc_fraud_train"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "index", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "trans_date_trans_time", "type": "TIMESTAMP", "mode": "NULLABLE"},
  {"name": "cc_num", "type": "STRING", "mode": "NULLABLE"},
  {"name": "merchant", "type": "STRING", "mode": "NULLABLE"},
  {"name": "category", "type": "STRING", "mode": "NULLABLE"},
  {"name": "amt", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "first", "type": "STRING", "mode": "NULLABLE"},
  {"name": "last", "type": "STRING", "mode": "NULLABLE"},
  {"name": "gender", "type": "STRING", "mode": "NULLABLE"},
  {"name": "street", "type": "STRING", "mode": "NULLABLE"},
  {"name": "city", "type": "STRING", "mode": "NULLABLE"},
  {"name": "state", "type": "STRING", "mode": "NULLABLE"},
  {"name": "zip", "type": "STRING", "mode": "NULLABLE"},
  {"name": "lat", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "long", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "city_pop", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "job", "type": "STRING", "mode": "NULLABLE"},
  {"name": "dob", "type": "DATE", "mode": "NULLABLE"},
  {"name": "trans_num", "type": "STRING", "mode": "NULLABLE"},
  {"name": "unix_time", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "merch_lat", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "merch_long", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "is_fraud", "type": "INTEGER", "mode": "NULLABLE"}
]
EOF
}

resource "google_bigquery_table" "cc_fraud_train" {
  dataset_id = google_bigquery_dataset.cc_fraud_dataset.dataset_id
  table_id = "cc_fraud_train"
  deletion_protection = false

  schema = <<EOF
[
  {"name": "cc_num", "type": "STRING", "mode": "NULLABLE"},
  {"name": "merchant", "type": "STRING", "mode": "NULLABLE"},
  {"name": "category", "type": "STRING", "mode": "NULLABLE"},
  {"name": "amt", "type": "FLOAT", "mode": "NULLABLE"},
  {"name": "city_pop", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "avg_transaction_val_24h", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "failed_attempts_count", "type": "INTEGER", "mode": "NULLABLE"},
  {"name": "feature_timestamp", "type": "TIMESTAMP", "mode": "NULLABLE"},
  {"name": "is_fraud", "type": "INTEGER", "mode": "NULLABLE"}
]
EOF
}

resource "random_id" "suffix" {
  byte_length = 4
}

resource "google_vertex_ai_feature_group" "cc_fraud_feature_store" {
  name = "cc_fraud_feature_store_${random_id.suffix.hex}"
  region = var.REGION

  big_query {
    big_query_source {
      input_uri = "bq://${google_bigquery_table.cc_fraud_train.project}.${google_bigquery_table.cc_fraud_train.dataset_id}.${google_bigquery_table.cc_fraud_train.table_id}"
    }
    entity_id_columns = ["cc_num"]
  }
}

resource "google_vertex_ai_feature_online_store" "cc_fraud_online_feature_store" {
  name = "cc_fraud_online_feature_store_${random_id.suffix.hex}"
  region = var.REGION

  bigtable {
    auto_scaling {
      min_node_count = 1
      max_node_count = 3
      cpu_utilization_target = 50
    }
  }
}

locals {
  feature_list = [
    "avg_transaction_val_24h",
    "failed_attempts_count",
    "merchant",
    "category",
    "amt",
    "city_pop",
    "is_fraud"
  ]
}

resource "google_vertex_ai_feature_group_feature" "cc_features" {
  for_each = toset(local.feature_list)

  name = each.value
  feature_group = google_vertex_ai_feature_group.cc_fraud_feature_store.name
  region = var.REGION
}

resource "google_vertex_ai_feature_online_store_featureview" "cc_fraud_view" {
  name = "cc_fraud_view_${random_id.suffix.hex}"
  region = var.REGION
  feature_online_store = google_vertex_ai_feature_online_store.cc_fraud_online_feature_store.name

  feature_registry_source {
    feature_groups {
      feature_group_id = google_vertex_ai_feature_group.cc_fraud_feature_store.name
      feature_ids = [for f in google_vertex_ai_feature_group_feature.cc_features : f.name]
    }
  }
}

resource "google_vertex_ai_endpoint" "cc-fraud-check" {
  name         = "cc-fraud-check"
  display_name = "CC fraud check"
  location     = var.REGION
}