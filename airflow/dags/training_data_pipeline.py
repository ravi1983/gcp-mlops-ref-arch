from datetime import datetime

from airflow.sdk import dag
import tasks.bigquery_pipeline_tasks as bq_tasks
import tasks.vertex_pipeline_tasks as vt_tasks


@dag(
    dag_id="process_training_data",
    start_date=datetime(2025, 4, 22),
    schedule=[bq_tasks.training_data_asset],
    catchup=False,
    tags=["ml", "training"],
)
def process_training_data():
    raw_task = bq_tasks.process_raw_data_task()
    poll_task = bq_tasks.poll_job_completion(raw_task)

    raw_task >> poll_task\
     >> bq_tasks.transform_raw_data() >> bq_tasks.create_snapshot_task()\
     >> vt_tasks.sync_feature_view() >> vt_tasks.kickoff_vertex_pipeline()

process_training_data()