import os
import pendulum
from google.ads.googleads.client import GoogleAdsClient
from ch_utils import get_client, ensure_table, insert_rows


DATASET = "google_ads"

CAMPAIGNS_COLUMNS = {
    "id": "String",
    "name": "String",
    "status": "String",
    "channel_type": "String",
    "start_date": "String",
    "end_date": "String",
    "budget_micros": "Int64",
}

PERFORMANCE_COLUMNS = {
    "date": "Date",
    "campaign_id": "String",
    "campaign_name": "String",
    "ad_group_id": "String",
    "ad_group_name": "String",
    "impressions": "Int64",
    "clicks": "Int64",
    "cost_micros": "Int64",
    "ctr": "Float64",
    "average_cpc": "Float64",
    "conversions": "Float64",
}


def _get_google_client() -> GoogleAdsClient:
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.environ["GOOGLE_ADS_DEVELOPER_TOKEN"],
        "client_id": os.environ["GOOGLE_CLIENT_ID"],
        "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
        "refresh_token": os.environ["GOOGLE_REFRESH_TOKEN"],
        "use_proto_plus": True,
    })


def extract_campaigns(customer_id: str) -> list[dict]:
    client = _get_google_client()
    ga_service = client.get_service("GoogleAdsService")
    query = """
        SELECT campaign.id, campaign.name, campaign.status,
               campaign.advertising_channel_type, campaign.start_date,
               campaign.end_date, campaign_budget.amount_micros
        FROM campaign ORDER BY campaign.id
    """
    rows = []
    for batch in ga_service.search_stream(customer_id=customer_id, query=query):
        for row in batch.results:
            rows.append({
                "id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "start_date": row.campaign.start_date,
                "end_date": row.campaign.end_date,
                "budget_micros": row.campaign_budget.amount_micros,
            })
    return rows


def extract_performance(customer_id: str) -> list[dict]:
    client = _get_google_client()
    ga_service = client.get_service("GoogleAdsService")
    yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")
    query = f"""
        SELECT segments.date, campaign.id, campaign.name,
               ad_group.id, ad_group.name, metrics.impressions,
               metrics.clicks, metrics.cost_micros, metrics.ctr,
               metrics.average_cpc, metrics.conversions
        FROM ad_group_ad WHERE segments.date = '{yesterday}'
    """
    rows = []
    for batch in ga_service.search_stream(customer_id=customer_id, query=query):
        for row in batch.results:
            rows.append({
                "date": row.segments.date,
                "campaign_id": str(row.campaign.id),
                "campaign_name": row.campaign.name,
                "ad_group_id": str(row.ad_group.id),
                "ad_group_name": row.ad_group.name,
                "impressions": row.metrics.impressions,
                "clicks": row.metrics.clicks,
                "cost_micros": row.metrics.cost_micros,
                "ctr": row.metrics.ctr,
                "average_cpc": row.metrics.average_cpc,
                "conversions": row.metrics.conversions,
            })
    return rows


if __name__ == "__main__":
    customer_id = os.environ["GOOGLE_ADS_CUSTOMER_ID"]

    client = get_client()
    client.command(f"CREATE DATABASE IF NOT EXISTS `{DATASET}`")
    ensure_table(client, DATASET, "campaigns", CAMPAIGNS_COLUMNS)
    ensure_table(client, DATASET, "ads_performance", PERFORMANCE_COLUMNS)

    campaigns = extract_campaigns(customer_id)
    n1 = insert_rows(client, DATASET, "campaigns", campaigns)
    print(f"✅ google_ads.campaigns: {n1} registros inseridos")

    performance = extract_performance(customer_id)
    n2 = insert_rows(client, DATASET, "ads_performance", performance)
    print(f"✅ google_ads.ads_performance: {n2} registros inseridos")

    print(f"✅ Google Ads concluído: {n1 + n2} registros totais")
