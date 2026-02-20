#!/bin/bash

gcloud functions deploy perform_inference \
  --gen2 \
  --runtime=python310 \
  --region=$REGION \
  --source=. \
  --entry-point=perform_inference \
  --trigger-http \
  --allow-unauthenticated
