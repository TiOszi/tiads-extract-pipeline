import os
import dlt
from dlt.sources.google_ads import google_ads_source

pipeline = dlt.pipeline(
    pipeline_name="google_ads",
    destination=dlt.destinations.clickhouse(
        credentials={
            "host": os.environ["CLICKHOUSE_HOST"],
            "database": os.environ["CLICKHOUSE_DATABASE"],
            "username": os.environ["CLICKHOUSE_USER"],
            "password": os.environ["CLICKHOUSE_PASSWORD"],
        }
    ),
    dataset_name="google_ads",
)

source = google_ads_source(
    customer_id=os.environ["GOOGLE_ADS_CUSTOMER_ID"],
    developer_token=os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
)

load_info = pipeline.run(source)
print(load_info)
