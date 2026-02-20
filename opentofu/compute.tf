data "archive_file" "dummy_zip" {
    type = "zip"
    output_path = "${path.module}/dummy.zip"

    source {
        content = "def perform_inference(request):\n    return 'OK'"
        filename = "main.py"
    }

    source {
        content = ""
        filename = "requirements.txt"
    }
}

resource "google_storage_bucket_object" "dummy_object" {
    name = "dummy_source_${data.archive_file.dummy_zip.output_md5}.zip"
    bucket = google_storage_bucket.ml_dataset.name
    source = data.archive_file.dummy_zip.output_path
}

resource "google_cloudfunctions2_function" "perform_inference" {
    name = "perform_inference"
    location = var.REGION

    build_config {
        runtime = "python310"
        entry_point = "perform_inference"

        source {
            storage_source {
                bucket = google_storage_bucket.ml_dataset.name
                object = google_storage_bucket_object.dummy_object.name
            }
        }
    }

    service_config {
        max_instance_count = 1
        available_memory = "256Mi"
        timeout_seconds = 60

        environment_variables = {
            PROJECT_ID: var.PROJECT_ID,
            LOCATION: var.REGION,
            ENDPOINT_ID: google_vertex_ai_endpoint.cc-fraud-check.id,
            FEATURE_ONLINE_STORE_ID: split("/", google_vertex_ai_feature_online_store.cc_fraud_online_feature_store.id)[5],
            FEATURE_VIEW_ID: split("/", google_vertex_ai_feature_online_store_featureview.cc_fraud_view.id)[7]
        }
    }

    lifecycle {
        ignore_changes = [
            build_config[0].source[0].storage_source[0].object,
            build_config[0].docker_repository,
            labels,
        ]
    }
}