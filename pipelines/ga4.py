import os
import dlt
from dlt.sources.google_analytics import google_analytics_source

pipeline = dlt.pipeline(
    pipeline_name="ga4",
    destination=dlt.destinations.clickhouse(
        credentials={
            "host": os.environ["CLICKHOUSE_HOST"],
            "database": os.environ["CLICKHOUSE_DATABASE"],
            "username": os.environ["CLICKHOUSE_USER"],
            "password": os.environ["CLICKHOUSE_PASSWORD"],
        }
    ),
    dataset_name="ga4",
)

source = google_analytics_source(
    property_id=os.environ["GA4_PROPERTY_ID"],
    client_id=os.environ["GOOGLE_CLIENT_ID"],
    client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
    refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
)

load_info = pipeline.run(source)
print(load_info)
