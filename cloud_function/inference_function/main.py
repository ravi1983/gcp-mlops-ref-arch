import os
import datetime

import functions_framework
from google.cloud import aiplatform
from google.cloud.aiplatform_v1 import FeatureOnlineStoreServiceClient
from google.cloud.aiplatform_v1.types import feature_online_store_service as gcap_service
from google.protobuf.json_format import MessageToDict

project_id = os.environ.get("PROJECT_ID")
location = os.environ.get("LOCATION")
endpoint_id = os.environ.get("ENDPOINT_ID")
feature_online_store_id = os.environ.get("FEATURE_ONLINE_STORE_ID")
feature_view_id = os.environ.get("FEATURE_VIEW_ID")

aiplatform.init(project=project_id, location=location)

data_client = FeatureOnlineStoreServiceClient(
    client_options={"api_endpoint": f"{location}-aiplatform.googleapis.com"}
)
feature_view_path = data_client.feature_view_path(
    project_id, location, feature_online_store_id, feature_view_id
)


def _transform_timestamp(timestamp):
    ts_micros = int(timestamp)
    ts_seconds = ts_micros / 1000000

    dt = datetime.datetime.fromtimestamp(ts_seconds, tz=datetime.timezone.utc)
    return dt.strftime('%Y-%m-%d %H:%M:%S%z')


@functions_framework.http
def perform_inference(request):
    request_json = request.get_json(silent=True)
    cc_num = str(request_json["cc_num"])
    print(f"Performing inference for card {cc_num}")

    data_request = gcap_service.FetchFeatureValuesRequest(
        feature_view=feature_view_path,
        data_key=gcap_service.FeatureViewDataKey(key=cc_num)
    )

    # Fetch features from feature store
    feature_response = data_client.fetch_feature_values(request=data_request)
    print(f"Fetched features for card {cc_num}: {feature_response}")

    # Transform features
    response_dict = MessageToDict(feature_response._pb)
    raw_features = response_dict.get('keyValues', {}).get('features', [])
    feature_dict = {item['name']: list(item['value'].values())[0] for item in raw_features}
    feature_dict['cc_num'] = cc_num
    feature_dict['feature_timestamp'] = _transform_timestamp(feature_dict['feature_timestamp'])
    print(f"Transformed features for card {cc_num}: {feature_dict}")

    # Inference
    endpoint = aiplatform.Endpoint(endpoint_id)
    prediction = endpoint.predict(instances=[feature_dict])
    return {
        "cc_num": cc_num,
        "prediction": prediction.predictions[0],
        "latency_optimized": True
    }
