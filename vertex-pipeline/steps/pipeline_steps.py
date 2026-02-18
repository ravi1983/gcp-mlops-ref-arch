from kfp import dsl
from google_cloud_pipeline_components.types import artifact_types
from google_cloud_pipeline_components.v1.automl.training_job import AutoMLTabularTrainingJobRunOp
from google_cloud_pipeline_components.v1.dataset.create_tabular_dataset.component import \
    tabular_dataset_create as TabularDatasetCreateOp
from google_cloud_pipeline_components.v1.endpoint.deploy_model.component import \
    model_deploy as ModelDeployOp


def create_dataset(project, location, dataset_name, snapshot_table_name):
    return TabularDatasetCreateOp(
        project=project,
        location=location,
        display_name=dataset_name,
        bq_source=snapshot_table_name
    )


def trigger_automl_training(project, location, training_name, import_dataset_op):
    return AutoMLTabularTrainingJobRunOp(
        project=project,
        location=location,
        display_name=training_name,
        optimization_prediction_type="classification",
        target_column="is_fraud",
        budget_milli_node_hours=1000,
        dataset=import_dataset_op.outputs['dataset']
    )


def import_inference_endpoint(location, endpoint_op):
    return dsl.importer(
        artifact_uri=f"https://{location}-aiplatform.googleapis.com/v1/{endpoint_op.outputs['endpoint']}",
        artifact_class=artifact_types.VertexEndpoint,
        metadata={"resourceName": endpoint_op.outputs['endpoint']}
    ).set_display_name('Import Inference Endpoint')


def deploy_model(model_artifact, endpoint):
    return ModelDeployOp(
        model=model_artifact,
        endpoint=endpoint,
        dedicated_resources_min_replica_count=1,
        dedicated_resources_machine_type="n1-standard-2",
        traffic_split={"0": 100}
    )
