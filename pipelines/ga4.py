import os
import dlt
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
)
from google.oauth2.credentials import Credentials
from typing import Iterator
import pendulum


def _get_client() -> BetaAnalyticsDataClient:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    return BetaAnalyticsDataClient(credentials=creds)


@dlt.source
def ga4_source(property_id: str):

    @dlt.resource(name="sessions_by_source", write_disposition="append")
    def sessions_by_source() -> Iterator[dict]:
        client = _get_client()
        yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="sessionSource"),
                Dimension(name="sessionMedium"),
                Dimension(name="sessionCampaignName"),
            ],
            metrics=[
                Metric(name="sessions"),
                Metric(name="bounceRate"),
                Metric(name="averageSessionDuration"),
                Metric(name="screenPageViews"),
            ],
            date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
        )

        response = client.run_report(request)
        dim_headers = [h.name for h in response.dimension_headers]
        met_headers = [h.name for h in response.metric_headers]

        for row in response.rows:
            record = {}
            for i, dim in enumerate(row.dimension_values):
                record[dim_headers[i]] = dim.value
            for i, met in enumerate(row.metric_values):
                record[met_headers[i]] = met.value
            yield record

    @dlt.resource(name="conversions", write_disposition="append")
    def conversions() -> Iterator[dict]:
        client = _get_client()
        yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")

        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=[
                Dimension(name="date"),
                Dimension(name="eventName"),
            ],
            metrics=[
                Metric(name="eventCount"),
                Metric(name="conversions"),
            ],
            date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
        )

        response = client.run_report(request)
        dim_headers = [h.name for h in response.dimension_headers]
        met_headers = [h.name for h in response.metric_headers]

        for row in response.rows:
            record = {}
            for i, dim in enumerate(row.dimension_values):
                record[dim_headers[i]] = dim.value
            for i, met in enumerate(row.metric_values):
                record[met_headers[i]] = met.value
            yield record

    return sessions_by_source, conversions


if __name__ == "__main__":
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

    source = ga4_source(
        property_id=os.environ["GA4_PROPERTY_ID"],
    )

    load_info = pipeline.run(source)
    print(load_info)
