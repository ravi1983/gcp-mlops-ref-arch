from kfp import dsl
from kfp.dsl import Input, Artifact, Output, Metrics, ClassificationMetrics


@dsl.component(base_image = "python:3.12", packages_to_install=["google-cloud-aiplatform"])
def log_model_metrics(model_artifact: Input[Artifact],
                      scalar_metrics: Output[Metrics],
                      classification_metrics: Output[ClassificationMetrics],
                      metrics_output: Output[Artifact]):
    import json
    import logging
    from google.cloud import aiplatform

    model_resource_name = model_artifact.metadata.get('resourceName')
    logging.info(f'Model resource name: {model_resource_name}')

    aiplatform.init(project='serverless-project-143', location='us-central1')
    model = aiplatform.Model(model_name=model_resource_name)

    def get_eval_info():
        response = model.list_model_evaluations()
        metrics = []
        metrics_values = []
        for evaluation in response:
            evaluation = evaluation.to_dict()
            eval_metrics = evaluation["metrics"]

            metrics.append(eval_metrics)
            metrics_values.append(json.dumps(metrics))

        return metrics

    def log_metrics(metrics_list):
        test_confusion_matrix = metrics_list[0]["confusionMatrix"]
        logging.info("rows: %s", test_confusion_matrix["rows"])

        # log the ROC curve
        fpr = []
        tpr = []
        thresholds = []
        for item in metrics_list[0]["confidenceMetrics"]:
            fpr.append(item.get("falsePositiveRate", 0.0))
            tpr.append(item.get("recall", 0.0))
            thresholds.append(item.get("confidenceThreshold", 0.0))

        classification_metrics.log_roc_curve(fpr, tpr, thresholds)
        logging.info("ROC curve logged.")

        # log the confusion matrix
        annotations = []
        for item in test_confusion_matrix["annotationSpecs"]:
            annotations.append(item["displayName"])
        classification_metrics.log_confusion_matrix(
            annotations,
            test_confusion_matrix["rows"],
        )
        logging.info("Confusion matrix logged.")

        # log textual metrics info as well
        for metric in metrics_list[0].keys():
            if metric != "confidenceMetrics":
                val_string = json.dumps(metrics_list[0][metric])
                scalar_metrics.log_metric(metric, val_string)

    metrics = get_eval_info()
    log_metrics(metrics)

    # This file will be used by the next component
    with open(metrics_output.path, 'w') as f:
        json.dump(metrics, f)
    logging.info("Metrics file saved as an artifact.")
