import os
import dlt
from google.ads.googleads.client import GoogleAdsClient
from typing import Iterator
import pendulum


def _ch_credentials() -> dict:
    return {
        "host": os.environ["CLICKHOUSE_HOST"],
        "database": os.environ["CLICKHOUSE_DATABASE"],
        "username": os.environ["CLICKHOUSE_USER"],
        "password": os.environ["CLICKHOUSE_PASSWORD"],
        "http_port": int(os.environ.get("CLICKHOUSE_HTTP_PORT", "8123")),
        "secure": bool(int(os.environ.get("CLICKHOUSE_SECURE", "0"))),
    }


def _get_google_client() -> GoogleAdsClient:
    config = {
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "use_proto_plus": True,
    }
    return GoogleAdsClient.load_from_dict(config)


@dlt.source
def google_ads_source(customer_id: str):

    @dlt.resource(name="campaigns", write_disposition="replace")
    def campaigns() -> Iterator[dict]:
        client = _get_google_client()
        ga_service = client.get_service("GoogleAdsService")
        query = """
            SELECT
                campaign.id,
                campaign.name,
                campaign.status,
                campaign.advertising_channel_type,
                campaign.start_date,
                campaign.end_date,
                campaign_budget.amount_micros
            FROM campaign
            ORDER BY campaign.id
        """
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in response:
            for row in batch.results:
                yield {
                    "id": row.campaign.id,
                    "name": row.campaign.name,
                    "status": row.campaign.status.name,
                    "channel_type": row.campaign.advertising_channel_type.name,
                    "start_date": row.campaign.start_date,
                    "end_date": row.campaign.end_date,
                    "budget_micros": row.campaign_budget.amount_micros,
                }

    @dlt.resource(name="ads_performance", write_disposition="append")
    def ads_performance() -> Iterator[dict]:
        client = _get_google_client()
        ga_service = client.get_service("GoogleAdsService")
        yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")
        query = f"""
            SELECT
                segments.date,
                campaign.id,
                campaign.name,
                ad_group.id,
                ad_group.name,
                metrics.impressions,
                metrics.clicks,
                metrics.cost_micros,
                metrics.ctr,
                metrics.average_cpc,
                metrics.conversions
            FROM ad_group_ad
            WHERE segments.date = '{yesterday}'
        """
        response = ga_service.search_stream(customer_id=customer_id, query=query)
        for batch in response:
            for row in batch.results:
                yield {
                    "date": row.segments.date,
                    "campaign_id": row.campaign.id,
                    "campaign_name": row.campaign.name,
                    "ad_group_id": row.ad_group.id,
                    "ad_group_name": row.ad_group.name,
                    "impressions": row.metrics.impressions,
                    "clicks": row.metrics.clicks,
                    "cost_micros": row.metrics.cost_micros,
                    "ctr": row.metrics.ctr,
                    "average_cpc": row.metrics.average_cpc,
                    "conversions": row.metrics.conversions,
                }

    return campaigns, ads_performance


if __name__ == "__main__":
    pipeline = dlt.pipeline(
        pipeline_name="google_ads",
        destination=dlt.destinations.clickhouse(
            credentials=_ch_credentials()
        ),
        dataset_name="google_ads",
    )

    source = google_ads_source(
        customer_id=os.environ["GOOGLE_ADS_CUSTOMER_ID"],
    )

    load_info = pipeline.run(source)
    print(load_info)
