import os
import pendulum
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import DateRange, Dimension, Metric, RunReportRequest
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from ch_utils import get_client, ensure_table, insert_rows


DATASET = "ga4"

SESSIONS_COLUMNS = {
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
    "date": "Date",
    "event_name": "String",
    "event_count": "Int64",
    "conversions": "Float64",
}


def _get_ga4_client() -> BetaAnalyticsDataClient:
    creds = Credentials(
        token=None,
        refresh_token=os.environ["GOOGLE_REFRESH_TOKEN"],
        client_id=os.environ["GOOGLE_CLIENT_ID"],
        client_secret=os.environ["GOOGLE_CLIENT_SECRET"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(Request())
    return BetaAnalyticsDataClient(credentials=creds)


def extract_sessions(property_id: str) -> list[dict]:
    client = _get_ga4_client()
    yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")
    response = client.run_report(RunReportRequest(
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
    rows = []
    for row in response.rows:
        d = [v.value for v in row.dimension_values]
        m = [v.value for v in row.metric_values]
        rows.append({
            "date": d[0], "session_source": d[1],
            "session_medium": d[2], "session_campaign_name": d[3],
            "sessions": int(m[0] or 0), "bounce_rate": float(m[1] or 0),
            "avg_session_duration": float(m[2] or 0), "page_views": int(m[3] or 0),
        })
    return rows


def extract_conversions(property_id: str) -> list[dict]:
    client = _get_ga4_client()
    yesterday = pendulum.now("America/Sao_Paulo").subtract(days=1).strftime("%Y-%m-%d")
    response = client.run_report(RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="date"), Dimension(name="eventName")],
        metrics=[Metric(name="eventCount"), Metric(name="conversions")],
        date_ranges=[DateRange(start_date=yesterday, end_date=yesterday)],
    ))
    rows = []
    for row in response.rows:
        d = [v.value for v in row.dimension_values]
        m = [v.value for v in row.metric_values]
        rows.append({
            "date": d[0], "event_name": d[1],
            "event_count": int(m[0] or 0), "conversions": float(m[1] or 0),
        })
    return rows


if __name__ == "__main__":
    property_id = os.environ["GA4_PROPERTY_ID"]

    client = get_client()
    client.command(f"CREATE DATABASE IF NOT EXISTS `{DATASET}`")
    ensure_table(client, DATASET, "sessions_by_source", SESSIONS_COLUMNS)
    ensure_table(client, DATASET, "conversions", CONVERSIONS_COLUMNS)

    sessions = extract_sessions(property_id)
    n1 = insert_rows(client, DATASET, "sessions_by_source", sessions)
    print(f"✅ ga4.sessions_by_source: {n1} registros inseridos")

    conversions = extract_conversions(property_id)
    n2 = insert_rows(client, DATASET, "conversions", conversions)
    print(f"✅ ga4.conversions: {n2} registros inseridos")

    print(f"✅ GA4 concluído: {n1 + n2} registros totais")
