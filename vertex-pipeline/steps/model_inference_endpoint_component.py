from typing import NamedTuple
from kfp import dsl

@dsl.component(base_image = "python:3.12", packages_to_install=["google-cloud-aiplatform", "google-cloud-pipeline-components"])
def model_inference_endpoint(project, location) -> NamedTuple('outputs', [('endpoint', str)]):
    from google.cloud import aiplatform
    from collections import namedtuple

    def get_or_create_endpoint(display_name: str):
        aiplatform.init(project=project, location=location)

        # Check for existing endpoints with this name
        endpoints = aiplatform.Endpoint.list(
            filter=f'display_name="{display_name}"',
            order_by="create_time desc"
        )

        if endpoints:
            endpoint = endpoints[0]
            print(f"Found existing endpoint: {endpoint.resource_name}")
        else:
            endpoint = aiplatform.Endpoint.create(display_name=display_name)
            print(f"Created new endpoint: {endpoint.resource_name}")
        return endpoint.resource_name

    endpoint_name = get_or_create_endpoint(display_name="cc-fraud-check")

    outputs = namedtuple("outputs", ["endpoint"])
    return outputs(endpoint=endpoint_name)
