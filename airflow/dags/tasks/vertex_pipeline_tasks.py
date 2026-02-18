import os
import time

from airflow.providers.google.cloud.operators.vertex_ai.feature_store import SyncFeatureViewOperator
from airflow.sdk import task
from google.cloud import aiplatform


def sync_feature_view():
    return SyncFeatureViewOperator(
        task_id='sync_feature_view',
        gcp_conn_id='google_cloud_default',
        project_id=os.environ.get('GCP_PROJECT'),
        location=os.environ.get('LOCATION'),
        feature_online_store_id=os.environ.get('FEATURE_ONLINE_STORE_ID'),
        feature_view_id=os.environ.get('FEATURE_VIEW_ID')
    )

@task
def kickoff_vertex_pipeline(snapshot_table_name):
    aiplatform.init(
        project = os.environ.get('GCP_PROJECT'),
        location = os.environ.get('LOCATION'),
    )
    timestamp = str(int(round(time.time() * 1000)))

    job = aiplatform.PipelineJob(
        display_name = "vertex-mlops-pipeline",
        template_path = os.environ.get('PIPELINE_TEMPLATE_PATH'),
        pipeline_root = os.environ.get('PIPELINE_ROOT_GCS'),
        parameter_values = {
            'project': os.environ.get('GCP_PROJECT'),
            'location': os.environ.get('LOCATION'),
            'snapshot_table_name': snapshot_table_name,
            'dataset_name': f'cc-fraud-dataset-{timestamp}',
            'training_name': f'cc-fraud-training-{timestamp}',
        },
        enable_caching = False,
    )

    job.submit() # Async invocation
    return job.resource_name