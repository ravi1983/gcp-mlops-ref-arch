import os

from airflow.providers.google.cloud.operators.vertex_ai.feature_store import SyncFeatureViewOperator
from airflow.providers.google.cloud.operators.vertex_ai.pipeline_job import RunPipelineJobOperator


def sync_feature_view():
    return SyncFeatureViewOperator(
        task_id='sync_feature_view',
        gcp_conn_id='google_cloud_default',
        project_id=os.environ.get('GCP_PROJECT'),
        location=os.environ.get('LOCATION'),
        feature_online_store_id=os.environ.get('FEATURE_ONLINE_STORE_ID'),
        feature_view_id=os.environ.get('FEATURE_VIEW_ID')
    )


def kickoff_vertex_pipeline():
    return RunPipelineJobOperator(
        task_id="kickoff_vertex_pipeline",
        project_id=os.environ.get('GCP_PROJECT'),
        region=os.environ.get('LOCATION'),
        display_name="vertex-mlops-pipeline",
        template_path=os.environ.get('PIPELINE_TEMPLATE_PATH'),
        pipeline_root=os.environ.get('PIPELINE_ROOT_GCS'),
        parameter_values={
            'project': os.environ.get('GCP_PROJECT'),
            'location': os.environ.get('LOCATION'),
            'snapshot_table_name': "{{ ti.xcom_pull(task_ids='create_snapshot_task') }}",
            'dataset_name': "cc-fraud-dataset-{{ macros.datetime.utcnow().strftime('%Y%m%dT%H%M%S') }}",
            'training_name': "cc-fraud-training-{{ macros.datetime.utcnow().strftime('%Y%m%dT%H%M%S') }}",
        },
        deferrable=True
    )
