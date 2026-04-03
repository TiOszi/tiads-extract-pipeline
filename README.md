# tiads-extract-pipeline

Pipeline de extração de dados de plataformas de mídia para ClickHouse (TiDash).

## Fontes
- Meta Ads (Facebook Marketing)
- Google Ads
- Google Analytics 4 (GA4)

## Destino
- ClickHouse (TiDash)

## Variáveis de ambiente necessárias

```env
CLICKHOUSE_HOST=
CLICKHOUSE_USER=
CLICKHOUSE_PASSWORD=
CLICKHOUSE_DATABASE=tidash

META_ADS_ACCESS_TOKEN=
META_ADS_ACCOUNT_ID=

GOOGLE_ADS_DEVELOPER_TOKEN=
GOOGLE_ADS_CUSTOMER_ID=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REFRESH_TOKEN=

GA4_PROPERTY_ID=
```

## Executar localmente

```bash
pip install -r requirements.txt
python pipelines/meta_ads.py
python pipelines/google_ads.py
python pipelines/ga4.py
```

## Build Docker

```bash
docker build -t tiads-extract-pipeline .
docker run --env-file .env tiads-extract-pipeline pipelines/meta_ads.py
```
