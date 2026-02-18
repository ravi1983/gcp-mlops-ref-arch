from typing import NamedTuple

from kfp import dsl
from kfp.dsl import Input, Artifact

@dsl.component(base_image = "python:3.12", packages_to_install=["google-cloud-aiplatform"])
def check_model_metrics(metrics_output: Input[Artifact]) -> NamedTuple('outputs', [('decision', str)]):
    import json
    import logging
    from collections import namedtuple

    with open(metrics_output.path, "r") as f:
        metrics = json.load(f)

    metric = metrics[0]
    au_roc = metric["auRoc"]
    logging.info(f"AUC ROC: {au_roc}")

    confidence_metrics = metric.get("confidenceMetrics", [])
    target_metrics = next((m for m in confidence_metrics if m.get("confidenceThreshold") == 0.8), confidence_metrics[0])
    fp_count = int(target_metrics.get("falsePositiveCount", 0))
    f1_score = target_metrics.get("f1Score", 0)
    logging.info(f"False positives: {fp_count}, F1 score: {f1_score}")

    # Check if ROC AUC and false positives are above threshold
    decision = "FAIL"
    if au_roc > 0.8 and (fp_count < 150 or f1_score > 0.75):
        decision = "PASS"

    outputs = namedtuple("outputs", ["decision"])
    return outputs(decision = decision)
