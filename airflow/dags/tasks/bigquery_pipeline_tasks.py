import logging
import os
import uuid
import time
from datetime import datetime, timedelta

from airflow.providers.google.cloud.hooks.bigquery import BigQueryHook
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator
from airflow.sdk import asset, task
from google.api_core.retry import Retry


@asset(
    uri='gs://ml_dataset_gr8/fraudTrain.csv',
    schedule=None,
)
def training_data_asset():
    logging.info('Training data asset created!')


@task(inlets=[training_data_asset])
def process_raw_data_task(inlet_events):
    result = inlet_events[training_data_asset][-1]
    logging.info(f"Asset URI to be loaded: {result.asset.uri}")

    hook = BigQueryHook(gcp_conn_id='google_cloud_default')
    job = hook.insert_job(
        configuration={
            "load": {
                "source_format": "CSV",
                "skip_leading_rows": 1,
                "destinationTable": {
                    "projectId": os.environ.get('GCP_PROJECT'),
                    "datasetId": os.environ.get('DATASET_ID'),
                    "tableId": os.environ.get('RAW_TABLE')
                },
                "sourceUris": [result.asset.uri],
                "writeDisposition": "WRITE_TRUNCATE"
            }
        },
        job_id=str(uuid.uuid4())
    )
    return job.job_id

@task
def poll_job_completion(job_id):
    logging.info(f"Polling job completion for job ID: {job_id}")
    hook = BigQueryHook(gcp_conn_id='google_cloud_default')
    return hook.poll_job_complete(
        job_id=job_id,
        project_id=os.environ.get('GCP_PROJECT'),
        location=os.environ.get('LOCATION'),
        retry=Retry(deadline=30)
    )

def transform_raw_data():
    return BigQueryInsertJobOperator(
        task_id='transform_raw_data',
        gcp_conn_id='google_cloud_default',
        location=os.environ.get('LOCATION'),
        configuration={
            'query': {
                'query': """
                    CREATE OR REPLACE TABLE `{{ params.project }}.{{ params.dataset }}.{{ params.feature_table }}` AS
                    SELECT
                        *,
                        -- Calculate 24h rolling average per card
                        AVG(amt) OVER (
                            PARTITION BY cc_num
                            ORDER BY UNIX_SECONDS(trans_date_trans_time)
                            RANGE BETWEEN 86400 PRECEDING AND CURRENT ROW
                        ) AS avg_transaction_val_24h,
                
                        -- Count failed attempts (assuming you have a status or is_fraud label)
                        COUNTIF(is_fraud = 1) OVER (
                            PARTITION BY cc_num
                            ORDER BY UNIX_SECONDS(trans_date_trans_time)
                            RANGE BETWEEN 86400 PRECEDING AND CURRENT ROW
                        ) AS failed_attempts_count,
                
                        -- Feature Store requirement
                        trans_date_trans_time AS feature_timestamp
                    FROM `{{ params.project }}.{{ params.dataset }}.{{ params.raw_table }}`
                """,
                'useLegacySql': False
            }
        },
        params={
            'project': os.environ.get('GCP_PROJECT'),
            'dataset': os.environ.get('DATASET_ID'),
            'raw_table': os.environ.get('RAW_TABLE'),
            'feature_table': os.environ.get('FEATURE_TABLE')
        },
        deferrable=True,
        poll_interval=10
    )

@task
def create_snapshot_task():
    project = os.environ.get("GCP_PROJECT")
    dataset = os.environ.get("DATASET_ID")
    feature_table = os.environ.get("FEATURE_TABLE")
    snapshot_name = f"{feature_table}_{int(time.time() * 1000)}"
    expiry = (datetime.now() + timedelta(days = 30)).strftime('%Y-%m-%d %H:%M:%S')

    hook = BigQueryHook(gcp_conn_id = 'google_cloud_default')

    job = hook.insert_job(
        configuration = {
            "query": {
                "query": f"""
                CREATE SNAPSHOT TABLE `{project}.{dataset}.{snapshot_name}`
                CLONE `{project}.{dataset}.{feature_table}`
                OPTIONS (
                    expiration_timestamp = TIMESTAMP '{expiry}'
                )
                """,
                "useLegacySql": False,
            }
        },
        location = os.environ.get('LOCATION', 'US')
    )
    print(f"Snapshot job {job.job_id} started for table {snapshot_name}")
    return snapshot_name
