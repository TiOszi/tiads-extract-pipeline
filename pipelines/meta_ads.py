"""
Meta Ads → ClickHouse
Credenciais lidas de ~/.dlt/secrets.toml via dlt.secrets
"""
import os
import sys
import dlt
import pendulum
from datetime import date
from facebook_business.api import FacebookAdsApi
from facebook_business.adobjects.adaccount import AdAccount
from facebook_business.adobjects.adsinsights import AdsInsights
from facebook_business.adobjects.campaign import Campaign
from ch_utils import get_client, ensure_table, insert_rows

DATASET = "meta_ads"

INSIGHTS_COLUMNS = {
    "account_id": "String",
    "client_slug": "String",
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
    "account_id": "String",
    "client_slug": "String",
    "id": "String",
    "name": "String",
    "status": "String",
    "objective": "String",
    "daily_budget": "Float64",
    "lifetime_budget": "Float64",
    "start_time": "String",
    "stop_time": "String",
}


def _to_date(value: str) -> date:
    if not value:
        return None
    return date.fromisoformat(value)


def run(account_id: str, client_slug: str):
    # Token lido do secrets.toml — não precisa ser passado pelo N8N
    access_token = dlt.secrets["meta_ads.access_token"]

    FacebookAdsApi.init(access_token=access_token)
    normalized_id = account_id.lstrip("act_").lstrip("ACT_")
    account = AdAccount(f"act_{normalized_id}")

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

    insights_rows = []
    for insight in account.get_insights(fields=fields, params=params):
        row = dict(insight)
        insights_rows.append({
            "account_id": account_id,
            "client_slug": client_slug,
            "date_start": _to_date(row.get("date_start")),
            "date_stop": _to_date(row.get("date_stop")),
            "campaign_id": str(row.get("campaign_id", "")),
            "campaign_name": str(row.get("campaign_name", "")),
            "adset_id": str(row.get("adset_id", "")),
            "adset_name": str(row.get("adset_name", "")),
            "ad_id": str(row.get("ad_id", "")),
            "ad_name": str(row.get("ad_name", "")),
            "impressions": int(row.get("impressions", 0) or 0),
            "clicks": int(row.get("clicks", 0) or 0),
            "spend": float(row.get("spend", 0) or 0),
            "reach": int(row.get("reach", 0) or 0),
            "cpm": float(row.get("cpm", 0) or 0),
            "cpc": float(row.get("cpc", 0) or 0),
            "ctr": float(row.get("ctr", 0) or 0),
        })

    campaign_rows = []
    for c in account.get_campaigns(fields=[
        Campaign.Field.id, Campaign.Field.name, Campaign.Field.status,
        Campaign.Field.objective, Campaign.Field.daily_budget,
        Campaign.Field.lifetime_budget, Campaign.Field.start_time,
        Campaign.Field.stop_time,
    ]):
        row = dict(c)
        campaign_rows.append({
            "account_id": account_id,
            "client_slug": client_slug,
            "id": str(row.get("id", "")),
            "name": str(row.get("name", "")),
            "status": str(row.get("status", "")),
            "objective": str(row.get("objective", "")),
            "daily_budget": float(row.get("daily_budget", 0) or 0) / 100,
            "lifetime_budget": float(row.get("lifetime_budget", 0) or 0) / 100,
            "start_time": str(row.get("start_time", "")),
            "stop_time": str(row.get("stop_time", "")),
        })

    ch = get_client()
    ensure_table(ch, DATASET, "ads_insights", INSIGHTS_COLUMNS)
    ensure_table(ch, DATASET, "campaigns", CAMPAIGNS_COLUMNS)
    n1 = insert_rows(ch, DATASET, "ads_insights", insights_rows)
    n2 = insert_rows(ch, DATASET, "campaigns", campaign_rows)
    print(f"✅ [{client_slug}] {n1} insights + {n2} campanhas → {DATASET}")
    return n1 + n2


if __name__ == "__main__":
    account_id  = os.environ.get("META_ADS_ACCOUNT_ID", "")
    client_slug = os.environ.get("CLIENT_SLUG", "default")

    if not account_id:
        print("❌ META_ADS_ACCOUNT_ID é obrigatório")
        sys.exit(1)

    total = run(account_id, client_slug)
    print(f"📊 Total: {total} registros")
