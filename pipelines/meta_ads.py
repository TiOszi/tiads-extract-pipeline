import os
import dlt
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from typing import Iterator
import pendulum

@dlt.source
def meta_ads_source(account_id: str, access_token: str):

    @dlt.resource(name="ads_insights", write_disposition="append")
    def ads_insights() -> Iterator[dict]:
        FacebookAdsApi.init(access_token=access_token)
        account = AdAccount(f"act_{account_id.lstrip('act_').lstrip('ACT_')}")

        fields = [
            AdsInsights.Field.date_start,
            AdsInsights.Field.date_stop,
            AdsInsights.Field.campaign_id,
            AdsInsights.Field.campaign_name,
            AdsInsights.Field.adset_id,
            AdsInsights.Field.adset_name,
            AdsInsights.Field.ad_id,
            AdsInsights.Field.ad_name,
            AdsInsights.Field.impressions,
            AdsInsights.Field.clicks,
            AdsInsights.Field.spend,
            AdsInsights.Field.reach,
            AdsInsights.Field.cpm,
            AdsInsights.Field.cpc,
            AdsInsights.Field.ctr,
        ]

        params = {
            "time_range": {
                "since": pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d"),
                "until": pendulum.now("America/Sao_Paulo").strftime("%Y-%m-%d"),
            },
            "level": "ad",
            "time_increment": 1,
        }

        insights = account.get_insights(fields=fields, params=params)
        for insight in insights:
            yield dict(insight)

    @dlt.resource(name="campaigns", write_disposition="replace")
    def campaigns() -> Iterator[dict]:
        from facebook_business.adobjects.campaign import Campaign
        FacebookAdsApi.init(access_token=access_token)
        account = AdAccount(f"act_{account_id.lstrip('act_').lstrip('ACT_')}")
        fields = [
            Campaign.Field.id,
            Campaign.Field.name,
            Campaign.Field.status,
            Campaign.Field.objective,
            Campaign.Field.daily_budget,
            Campaign.Field.lifetime_budget,
            Campaign.Field.start_time,
            Campaign.Field.stop_time,
        ]
        for campaign in account.get_campaigns(fields=fields):
            yield dict(campaign)

    return ads_insights, campaigns


if __name__ == "__main__":
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

    source = meta_ads_source(
        account_id=os.environ["META_ADS_ACCOUNT_ID"],
        access_token=os.environ["META_ADS_ACCESS_TOKEN"],
    )

    load_info = pipeline.run(source)
    print(load_info)
