#!/bin/bash

# Generate keys for astro
gcloud iam service-accounts keys create ./include/gcp-key.json \
    --iam-account=mlops-service-account@$PROJECT_ID.iam.gserviceaccount.com