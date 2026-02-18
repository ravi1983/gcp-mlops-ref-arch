import google.cloud.aiplatform as aiplatform
from kfp import compiler
from cc_fraud_detection_model_pipeline import cc_fraud_detection_model_pipeline

# compiler.Compiler().compile(
#     pipeline_func=cc_fraud_detection_model_pipeline,
#     package_path="cc_fraud_detection_model_pipeline.json",
# )

job = aiplatform.PipelineJob(
    display_name='AutoML_CC_Fraud_Task-67891-1',
    template_path='cc_fraud_detection_model_pipeline.json',
    enable_caching=True,
    parameter_values={}
)
job.submit(
    service_account='',
    experiment='cc-fraud-detection-experiments'
)