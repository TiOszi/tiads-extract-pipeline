import os
import pendulum
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.campaign import Campaign
from ch_utils import get_client, ensure_table, insert_rows


DATASET = "meta_ads"

INSIGHTS_COLUMNS = {
    "date_start": "Date",
    "date_stop": "Date",
    "campaign_id": "String",
    "campaign_name": "String",
    "adset_id": "String",
    "adset_name": "String",
    "ad_id": "String",
    "ad_name": "String",
    "impressions": "Int64",
    "clicks": "Int64",
    "spend": "Float64",
    "reach": "Int64",
    "cpm": "Float64",
    "cpc": "Float64",
    "ctr": "Float64",
}

CAMPAIGNS_COLUMNS = {
    "id": "String",
    "name": "String",
    "status": "String",
    "objective": "String",
    "daily_budget": "Float64",
    "lifetime_budget": "Float64",
    "start_time": "String",
    "stop_time": "String",
}


def extract_insights(account_id: str, access_token: str) -> list[dict]:
    FacebookAdsApi.init(access_token=access_token)
    account = AdAccount(f"act_{account_id.lstrip('act_').lstrip('ACT_')}")

    fields = [
        AdsInsights.Field.date_start, AdsInsights.Field.date_stop,
        AdsInsights.Field.campaign_id, AdsInsights.Field.campaign_name,
        AdsInsights.Field.adset_id, AdsInsights.Field.adset_name,
        AdsInsights.Field.ad_id, AdsInsights.Field.ad_name,
        AdsInsights.Field.impressions, AdsInsights.Field.clicks,
        AdsInsights.Field.spend, AdsInsights.Field.reach,
        AdsInsights.Field.cpm, AdsInsights.Field.cpc, AdsInsights.Field.ctr,
    ]

    params = {
        "time_range": {
            "since": pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d"),
            "until": pendulum.now("America/Sao_Paulo").strftime("%Y-%m-%d"),
        },
        "level": "ad",
        "time_increment": 1,
    }

    rows = []
    for insight in account.get_insights(fields=fields, params=params):
        row = dict(insight)
        row["impressions"] = int(row.get("impressions", 0) or 0)
        row["clicks"] = int(row.get("clicks", 0) or 0)
        row["reach"] = int(row.get("reach", 0) or 0)
        row["spend"] = float(row.get("spend", 0) or 0)
        row["cpm"] = float(row.get("cpm", 0) or 0)
        row["cpc"] = float(row.get("cpc", 0) or 0)
        row["ctr"] = float(row.get("ctr", 0) or 0)
        rows.append({k: row.get(k) for k in INSIGHTS_COLUMNS})
    return rows


def extract_campaigns(account_id: str, access_token: str) -> list[dict]:
    FacebookAdsApi.init(access_token=access_token)
    account = AdAccount(f"act_{account_id.lstrip('act_').lstrip('ACT_')}")
    fields = [
        Campaign.Field.id, Campaign.Field.name, Campaign.Field.status,
        Campaign.Field.objective, Campaign.Field.daily_budget,
        Campaign.Field.lifetime_budget, Campaign.Field.start_time,
        Campaign.Field.stop_time,
    ]
    rows = []
    for c in account.get_campaigns(fields=fields):
        row = dict(c)
        row["daily_budget"] = float(row.get("daily_budget", 0) or 0) / 100
        row["lifetime_budget"] = float(row.get("lifetime_budget", 0) or 0) / 100
        rows.append({k: str(row.get(k, "")) for k in CAMPAIGNS_COLUMNS})
    return rows


if __name__ == "__main__":
    account_id = os.environ["META_ADS_ACCOUNT_ID"]
    access_token = os.environ["META_ADS_ACCESS_TOKEN"]

    client = get_client()
    client.command(f"CREATE DATABASE IF NOT EXISTS `{DATASET}`")
    ensure_table(client, DATASET, "ads_insights", INSIGHTS_COLUMNS)
    ensure_table(client, DATASET, "campaigns", CAMPAIGNS_COLUMNS)

    insights = extract_insights(account_id, access_token)
    n1 = insert_rows(client, DATASET, "ads_insights", insights)
    print(f"✅ meta_ads.ads_insights: {n1} registros inseridos")

    campaigns = extract_campaigns(account_id, access_token)
    n2 = insert_rows(client, DATASET, "campaigns", campaigns)
    print(f"✅ meta_ads.campaigns: {n2} registros inseridos")

    print(f"✅ Meta Ads concluído: {n1 + n2} registros totais")
