import os
import clickhouse_connect
from clickhouse_connect.driver.client import Client


def get_client() -> Client:
    """Retorna cliente ClickHouse via HTTP (porta 8123)."""
    return clickhouse_connect.get_client(
        host=os.environ["CLICKHOUSE_HOST"],
        port=int(os.environ.get("CLICKHOUSE_HTTP_PORT", "8123")),
        username=os.environ["CLICKHOUSE_USER"],
        password=os.environ["CLICKHOUSE_PASSWORD"],
        database=os.environ["CLICKHOUSE_DATABASE"],
        secure=False,
    )


def ensure_table(client: Client, dataset: str, table: str, columns: dict) -> None:
    """Cria tabela no ClickHouse se não existir."""
    cols_ddl = ",\n    ".join(
        f"`{col}` {dtype}" for col, dtype in columns.items()
    )
    client.command(f"""
        CREATE TABLE IF NOT EXISTS `{dataset}`.`{table}` (
            {cols_ddl},
            `_loaded_at` DateTime DEFAULT now()
        )
        ENGINE = MergeTree()
        ORDER BY tuple()
    """)


def insert_rows(client: Client, dataset: str, table: str, rows: list[dict]) -> int:
    """Insere lista de dicts numa tabela ClickHouse. Retorna qtd inserida."""
    if not rows:
        return 0
    columns = list(rows[0].keys())
    data = [[row.get(col) for col in columns] for row in rows]
    client.insert(f"`{dataset}`.`{table}`", data, column_names=columns)
    return len(rows)
