# End-to-End MLOps Reference Architecture on GCP

Production-grade reference architecture for building, training, evaluating, and deploying machine learning models on Google Cloud Platform using OpenTofu, BigQuery, Airflow, Vertex AI, and Vertex AI Feature Store.

This repository demonstrates a complete MLOps workflow using the Kaggle Credit Card Fraud Detection dataset as a working example.

---

## Overview

This project implements a fully automated, event-driven MLOps architecture that:

1. Provisions infrastructure using OpenTofu.
2. Ingests and transforms data using Airflow and BigQuery.
3. Maintains data lineage via BigQuery table snapshots.
4. Trains and evaluates models using Vertex AI Pipelines and AutoML.
5. Deploys models to a Vertex AI online endpoint based on performance thresholds.
6. Serves real-time predictions through a Cloud Function API.
7. Retrieves online features from Vertex AI Feature Store for inference consistency.

The architecture supports continuous training, automated evaluation, and conditional deployment.

---

## Architecture

### End-to-End Flow

1. Data lands in Google Cloud Storage (GCS).
2. Airflow DAG is triggered on object create/update event.
3. Data is copied into a raw BigQuery table.
4. Data is transformed and loaded into a training table.
5. A snapshot of the training table is created to preserve lineage and reproducibility.
6. Feature View is synchronized.
7. Vertex AI Pipeline is triggered.
8. Vertex Pipeline:
   - Creates a dataset from the snapshot.
   - Runs AutoML training.
   - Evaluates model metrics.
   - If performance meets threshold, deploys model to endpoint.
9. Cloud Function API:
   - Accepts card number as input.
   - Fetches features from Feature Store.
   - Calls deployed model endpoint.
   - Returns fraud prediction.

---

## Architecture Diagram

PLACEHOLDER: INSERT DESIGN DIAGRAM IMAGE HERE

---

## Infrastructure as Code (OpenTofu)

OpenTofu provisions the following resources:

- BigQuery datasets (raw and training)
- BigQuery tables
- BigQuery snapshot table
- Service accounts
- IAM bindings
- Cloud Function
- Vertex AI Feature Store
- Feature View
- Vertex AI pipeline components
- Required project-level configurations

Infrastructure is declarative and reproducible.

---

## Data Pipeline (Airflow)

Airflow DAG is triggered when an object is created or updated in GCS.

### DAG Steps

1. Load incoming file into BigQuery raw table.
2. Transform raw table into training table.
3. Create snapshot of training table.
   - Enables data lineage.
   - Ensures reproducibility.
4. Sync Feature View.
5. Trigger Vertex AI Pipeline.

Snapshots ensure that every model version is traceable to a specific immutable dataset.

---

## Model Training and Deployment (Vertex AI)

The Vertex AI Pipeline performs:

1. Dataset creation from BigQuery snapshot.
2. AutoML training job execution.
3. Model evaluation against defined metrics (e.g., AUC, precision, recall).
4. Threshold comparison logic.
5. Conditional deployment:
   - Register model.
   - Deploy to Vertex AI endpoint if threshold is met.

This enables automated promotion of models based on measurable performance.

---

## Online Inference Architecture

The Cloud Function acts as the API entry point for predictions.

### Inference Flow

1. Accept card_number as input.
2. Retrieve features from Vertex AI Feature Store using Feature View.
3. Call deployed Vertex AI endpoint with card number and features.
4. Return prediction response to caller.

This guarantees feature parity between training and serving environments.

---

## Repository Structure

.
├── opentofu/              # Infrastructure as Code definitions  
├── airflow/               # DAG definitions  
├── vertex_pipeline/       # Training and evaluation pipeline components  
├── cloud_function/        # Inference API implementation  
├── sql/                   # Transformation queries  
├── diagrams/              # Architecture diagrams  
└── README.md  

---

## Dataset

Source: Kaggle Credit Card Fraud Detection Dataset.

- Binary classification problem.
- Highly imbalanced dataset.
- Used to demonstrate fraud detection use case in a production-style MLOps architecture.

---

## Production Readiness Callouts

Before using this architecture in production, address the following critical items:

### 1. Enforce Least Privilege for Service Accounts

- Avoid broad project-level roles.
- Scope IAM at dataset, table, pipeline, and endpoint level.
- Separate service accounts for:
  - Training
  - Pipeline orchestration
  - Feature Store access
  - Inference
- Remove unused permissions.

### 2. Enable Canary Deployment for Model Releases

- Do not route 100% traffic immediately.
- Use Vertex Endpoint traffic splitting.
- Gradually increase traffic to new model version.
- Monitor performance before full rollout.

### 3. Enable Model Monitoring

- Configure Vertex Model Monitoring.
- Track feature skew and drift.
- Track prediction distribution drift.
- Configure alerts through Cloud Monitoring.
- Continuously validate production model health.

### 4. Optimize Online Feature Store for Spiky Requests

- Configure online serving capacity appropriately.
- Tune scaling configuration for burst traffic.
- Load test inference endpoints.
- Balance latency and throughput requirements.

---

## Continuous MLOps Capabilities

This architecture supports:

- Event-driven retraining.
- Automated evaluation and conditional deployment.
- Immutable dataset snapshots for lineage.
- Feature consistency between offline and online paths.
- Infrastructure as Code reproducibility.
- Modular and extensible pipeline design.

---

## Prerequisites

- Google Cloud Project.
- OpenTofu installed.
- gcloud CLI configured.
- Python 3.10+.
- Airflow environment.
- Vertex AI API enabled.
- BigQuery API enabled.
- Cloud Functions API enabled.

---

## Deployment Steps

1. Initialize OpenTofu:

   tofu init

2. Apply infrastructure:

   tofu apply

3. Deploy Airflow DAGs to your Airflow environment.

4. Deploy Cloud Function:

   gcloud functions deploy <FUNCTION_NAME> --runtime python310 --trigger-http --allow-unauthenticated

---

## Security Considerations

- Use CMEK if regulatory requirements demand it.
- Restrict network egress where possible.
- Enable audit logging.
- Avoid long-lived service account keys.
- Apply VPC Service Controls if required.
- Enable Cloud Monitoring and alerting.

---

## Design Principles

- Infrastructure as Code first.
- Immutable training datasets.
- Event-driven architecture.
- Automated governance.
- Continuous evaluation.
- Separation of concerns.
- Reproducibility and traceability.

---

## Future Enhancements

- CI/CD integration for pipeline validation.
- Blue/Green model deployment strategy.
- Automated rollback workflows.
- Feature registry governance workflows.
- Cost monitoring dashboards.
- Metadata tracking visualization.

---

## License

Specify your preferred license (e.g., MIT License).

---

## Contributions

Contributions are welcome. Please open issues or submit pull requests.

---

This repository serves as a reference implementation for scalable, production-ready MLOps on Google Cloud Platform. It is designed as a foundation and should be hardened appropriately before enterprise deployment.
