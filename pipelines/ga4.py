"""
GA4 → ClickHouse (dataset único: ga4)
property_id e client_slug são colunas nas tabelas
"""
import os
import sys
import pendulum
from datetime import date
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from ch_utils import get_client, ensure_table, insert_rows

DATASET = "ga4"

SESSIONS_COLUMNS = {
    "property_id": "String",
    "client_slug": "String",
    "date": "Date",
    "session_source": "String",
    "session_medium": "String",
    "session_campaign_name": "String",
    "sessions": "Int64",
    "bounce_rate": "Float64",
    "avg_session_duration": "Float64",
    "page_views": "Int64",
}

CONVERSIONS_COLUMNS = {
    "property_id": "String",
    "client_slug": "String",
    "date": "Date",
    "event_name": "String",
    "event_count": "Int64",
    "conversions": "Float64",
}


def _to_date(value: str) -> date:
    """Converte string 'YYYYMMDD' ou 'YYYY-MM-DD' para datetime.date."""
    if not value:
        return None
    value = value.replace("-", "")
    return date(int(value[:4]), int(value[4:6]), int(value[6:8]))


def _build_ga4_client() -> BetaAnalyticsDataClient:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return BetaAnalyticsDataClient(credentials=creds)


def run(property_id: str, client_slug: str):
    client = _build_ga4_client()
    yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")

    # --- Sessions ---
    resp = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[
            Dimension(name="date"), Dimension(name="sessionSource"),
            Dimension(name="sessionMedium"), Dimension(name="sessionCampaignName"),
        ],
        metrics=[
            Metric(name="sessions"), Metric(name="bounceRate"),
            Metric(name="averageSessionDuration"), Metric(name="screenPageViews"),
        ],
        date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
    ))
    sessions_rows = []
    for row in resp.rows:
        d = [v.value for v in row.dimension_values]
        m = [v.value for v in row.metric_values]
        sessions_rows.append({
            "property_id": property_id,
            "client_slug": client_slug,
            "date": _to_date(d[0]),
            "session_source": d[1],
            "session_medium": d[2],
            "session_campaign_name": d[3],
            "sessions": int(m[0] or 0),
            "bounce_rate": float(m[1] or 0),
            "avg_session_duration": float(m[2] or 0),
            "page_views": int(m[3] or 0),
        })

    # --- Conversions ---
    resp2 = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date"), Dimension(name="eventName")],
        metrics=[Metric(name="eventCount"), Metric(name="conversions")],
        date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
    ))
    conversion_rows = []
    for row in resp2.rows:
        d = [v.value for v in row.dimension_values]
        m = [v.value for v in row.metric_values]
        conversion_rows.append({
            "property_id": property_id,
            "client_slug": client_slug,
            "date": _to_date(d[0]),
            "event_name": d[1],
            "event_count": int(m[0] or 0),
            "conversions": float(m[1] or 0),
        })

    ch = get_client()
    ensure_table(ch, DATASET, "sessions_by_source", SESSIONS_COLUMNS)
    ensure_table(ch, DATASET, "conversions", CONVERSIONS_COLUMNS)
    n1 = insert_rows(ch, DATASET, "sessions_by_source", sessions_rows)
    n2 = insert_rows(ch, DATASET, "conversions", conversion_rows)
    print(f"✅ [{client_slug}] {n1} sessões + {n2} conversões → {DATASET}")
    return n1 + n2


if __name__ == "__main__":
    property_id = os.environ.get("GA4_PROPERTY_ID", "")
    client_slug = os.environ.get("CLIENT_SLUG", "default")

    if not property_id:
        print("❌ GA4_PROPERTY_ID é obrigatório")
        sys.exit(1)

    total = run(property_id, client_slug)
    print(f"📊 Total: {total} registros")
