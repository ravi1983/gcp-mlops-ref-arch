import logging

from kfp import dsl

import steps.pipeline_steps as steps

from steps.log_model_metrics_component import log_model_metrics
from steps.check_model_metrics_component import check_model_metrics
from steps.model_inference_endpoint_component import model_inference_endpoint


@dsl.pipeline(name='cc_fraud_detection_model_pipeline', pipeline_root='gs://pipeline-artifacts-789y74/pipeline_root')
def cc_fraud_detection_model_pipeline(
    project: str,
    location: str,
    snapshot_table_name: str,
    dataset_name: str,
    training_name: str,
):
    # Train model
    dataset = steps.create_dataset(project, location, dataset_name, snapshot_table_name)
    training_op = steps.trigger_automl_training(project, location, training_name, dataset)
    training_op.container_spec.image_uri = "gcr.io/ml-pipeline/google-cloud-pipeline-components:2.16.1"

    # Eval and log model
    default_metrics_log_op = log_model_metrics(model_artifact=training_op.outputs['model'])
    check_op = check_model_metrics(
        metrics_output=default_metrics_log_op.outputs['metrics_output']
    )

    # Validate and deploy model
    with dsl.If(check_op.outputs['decision'] == 'PASS', name='deploy_decision'):
        endpoint_op = model_inference_endpoint(project=project, location=location)
        logging.info(f"Endpoint created: {endpoint_op}")

        inference_op = steps.import_inference_endpoint(location, endpoint_op)
        steps.deploy_model(training_op.outputs['model'], inference_op.outputs['artifact'])
