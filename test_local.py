"""
Script de teste local — roda os pipelines sem Docker.
Uso: python test_local.py meta_ads
     python test_local.py google_ads
     python test_local.py ga4
     python test_local.py all
"""
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega .env da raiz do projeto (apenas META_ADS_ACCOUNT_ID, CLIENT_SLUG, etc.)
load_dotenv(Path(__file__).parent / ".env")

# Adiciona pipelines/ ao path
sys.path.insert(0, str(Path(__file__).parent / "pipelines"))

def test_clickhouse():
    print("\n🔌 Testando conexão ClickHouse...")
    from ch_utils import get_client
    client = get_client()
    result = client.query("SELECT version()")
    print(f"✅ ClickHouse conectado — versão: {result.result_rows[0][0]}")
    return True

def test_meta_ads():
    print("\n📘 Testando Meta Ads...")
    import meta_ads
    # access_token agora vem do .dlt/secrets.toml automaticamente
    total = meta_ads.run(
        account_id=os.environ["META_ADS_ACCOUNT_ID"],
        client_slug=os.environ.get("CLIENT_SLUG", "teste"),
    )
    print(f"✅ Meta Ads OK — {total} registros")

def test_google_ads():
    print("\n🟢 Testando Google Ads...")
    import google_ads
    total = google_ads.run(
        customer_id=os.environ["GOOGLE_ADS_CUSTOMER_ID"],
        client_slug=os.environ.get("CLIENT_SLUG", "teste"),
    )
    print(f"✅ Google Ads OK — {total} registros")

def test_ga4():
    print("\n📊 Testando GA4...")
    import ga4
    total = ga4.run(
        property_id=os.environ["GA4_PROPERTY_ID"],
        client_slug=os.environ.get("CLIENT_SLUG", "teste"),
    )
    print(f"✅ GA4 OK — {total} registros")

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "all"

    try:
        test_clickhouse()
    except Exception as e:
        print(f"❌ ClickHouse falhou: {e}")
        sys.exit(1)

    if target in ("meta_ads", "all"):
        try:
            test_meta_ads()
        except Exception as e:
            print(f"❌ Meta Ads falhou: {e}")

    if target in ("google_ads", "all"):
        if os.environ.get("GOOGLE_ADS_CUSTOMER_ID"):
            try:
                test_google_ads()
            except Exception as e:
                print(f"❌ Google Ads falhou: {e}")
        else:
            print("⏭️  Google Ads pulado (GOOGLE_ADS_CUSTOMER_ID não definido)")

    if target in ("ga4", "all"):
        if os.environ.get("GA4_PROPERTY_ID"):
            try:
                test_ga4()
            except Exception as e:
                print(f"❌ GA4 falhou: {e}")
        else:
            print("⏭️  GA4 pulado (GA4_PROPERTY_ID não definido)")
