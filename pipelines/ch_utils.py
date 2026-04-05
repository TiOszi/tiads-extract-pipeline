import os
import clickhouse_connect
from clickhouse_connect.driver.client import Client
import dlt


def get_client() -> Client:
    """Retorna cliente ClickHouse via HTTP (porta 8123) usando dlt.secrets."""
    return clickhouse_connect.get_client(
        host=dlt.secrets["clickhouse.host"],
        port=int(dlt.secrets["clickhouse.http_port"]),
        username=dlt.secrets["clickhouse.username"],
        password=dlt.secrets["clickhouse.password"],
        database=dlt.secrets["clickhouse.database"],
        secure=False,
    )


def ensure_table(client: Client, dataset: str, table: str, columns: dict) -> None:
    """Cria banco e tabela no ClickHouse se não existirem."""
    client.command(f"CREATE DATABASE IF NOT EXISTS `{dataset}`")
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
    existing = {
        row[0]
        for row in client.query(
            f"DESCRIBE TABLE `{dataset}`.`{table}`"
        ).result_rows
    }
    for col, dtype in columns.items():
        if col not in existing:
            client.command(
                f"ALTER TABLE `{dataset}`.`{table}` ADD COLUMN IF NOT EXISTS `{col}` {dtype}"
            )
            print(f"  ↳ coluna adicionada: {col} ({dtype})")


def insert_rows(client: Client, dataset: str, table: str, rows: list[dict]) -> int:
    """Insere lista de dicts numa tabela ClickHouse. Retorna qtd inserida."""
    if not rows:
        return 0
    columns = list(rows[0].keys())
    data = [[row.get(col) for col in columns] for row in rows]
    client.insert(f"`{dataset}`.`{table}`", data, column_names=columns)
    return len(rows)
