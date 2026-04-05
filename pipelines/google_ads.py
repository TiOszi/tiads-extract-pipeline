"""
Google Ads → ClickHouse
Credenciais lidas de ~/.dlt/secrets.toml via dlt.secrets
"""
import os
import sys
import dlt
import pendulum
from google.ads.googleads.client import GoogleAdsClient
from ch_utils import get_client, ensure_table, insert_rows

DATASET = "google_ads"

CAMPAIGNS_COLUMNS = {
    "customer_id": "String",
    "client_slug": "String",
    "id": "String",
    "name": "String",
    "status": "String",
    "channel_type": "String",
    "start_date": "String",
    "end_date": "String",
    "budget_micros": "Int64",
}

PERFORMANCE_COLUMNS = {
    "customer_id": "String",
    "client_slug": "String",
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


def _build_google_client() -> GoogleAdsClient:
    return GoogleAdsClient.load_from_dict({
        "developer_token": dlt.secrets["google_ads.developer_token"],
        "client_id": dlt.secrets["google.client_id"],
        "client_secret": dlt.secrets["google.client_secret"],
        "refresh_token": dlt.secrets["google.refresh_token"],
        "use_proto_plus": True,
    })


def run(customer_id: str, client_slug: str):
    from datetime import date
    normalized_id = customer_id.replace("-", "")
    gads = _build_google_client()
    ga_service = gads.get_service("GoogleAdsService")

    campaign_rows = []
    for batch in ga_service.search_stream(customer_id=normalized_id, query="""
        SELECT campaign.id, campaign.name, campaign.status,
               campaign.advertising_channel_type, campaign.start_date,
               campaign.end_date, campaign_budget.amount_micros
        FROM campaign ORDER BY campaign.id
    """):
        for row in batch.results:
            campaign_rows.append({
                "customer_id": customer_id,
                "client_slug": client_slug,
                "id": str(row.campaign.id),
                "name": row.campaign.name,
                "status": row.campaign.status.name,
                "channel_type": row.campaign.advertising_channel_type.name,
                "start_date": row.campaign.start_date,
                "end_date": row.campaign.end_date,
                "budget_micros": row.campaign_budget.amount_micros,
            })

    yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")
    performance_rows = []
    for batch in ga_service.search_stream(customer_id=normalized_id, query=f"""
        SELECT segments.date, campaign.id, campaign.name,
               ad_group.id, ad_group.name, metrics.impressions,
               metrics.clicks, metrics.cost_micros, metrics.ctr,
               metrics.average_cpc, metrics.conversions
        FROM ad_group_ad WHERE segments.date = '{yesterday}'
    """):
        for row in batch.results:
            performance_rows.append({
                "customer_id": customer_id,
                "client_slug": client_slug,
                "date": date.fromisoformat(row.segments.date),
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

    ch = get_client()
    ensure_table(ch, DATASET, "campaigns", CAMPAIGNS_COLUMNS)
    ensure_table(ch, DATASET, "ads_performance", PERFORMANCE_COLUMNS)
    n1 = insert_rows(ch, DATASET, "campaigns", campaign_rows)
    n2 = insert_rows(ch, DATASET, "ads_performance", performance_rows)
    print(f"✅ [{client_slug}] {n1} campanhas + {n2} performance → {DATASET}")
    return n1 + n2


if __name__ == "__main__":
    customer_id = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "")
    client_slug = os.environ.get("CLIENT_SLUG", "default")

    if not customer_id:
        print("❌ GOOGLE_ADS_CUSTOMER_ID é obrigatório")
        sys.exit(1)

    total = run(customer_id, client_slug)
    print(f"📊 Total: {total} registros")
