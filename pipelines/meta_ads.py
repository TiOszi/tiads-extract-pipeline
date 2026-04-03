import os
import dlt
from dlt.sources.facebook_ads import facebook_ads_source

pipeline = dlt.pipeline(
    pipeline_name="meta_ads",
    destination=dlt.destinations.clickhouse(
        credentials={
            "host": os.environ["CLICKHOUSE_HOST"],
            "database": os.environ["CLICKHOUSE_DATABASE"],
            "username": os.environ["CLICKHOUSE_USER"],
            "password": os.environ["CLICKHOUSE_PASSWORD"],
        }
    ),
    dataset_name="meta_ads",
)

source = facebook_ads_source(
    account_id=os.environ["META_ADS_ACCOUNT_ID"],
    access_token=os.environ["META_ADS_ACCESS_TOKEN"],
)

load_info = pipeline.run(source)
print(load_info)
