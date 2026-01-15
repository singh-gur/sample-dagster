"""Sample Dagster assets demonstrating basic ETL patterns."""

import pandas as pd
from dagster import asset

from sample_dagster.resources import DuckDBResource


@asset
def raw_customers(duckdb: DuckDBResource) -> None:
    """Ingest raw customer data into the database."""
    # Sample data for demonstration
    data = {
        "customer_id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
        "email": [
            "alice@example.com",
            "bob@example.com",
            "charlie@example.com",
            "diana@example.com",
            "eve@example.com",
        ],
        "signup_date": ["2024-01-15", "2024-02-20", "2024-03-10", "2024-04-05", "2024-05-01"],
    }
    df = pd.DataFrame(data)

    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute("CREATE TABLE IF NOT EXISTS raw.customers AS SELECT * FROM df LIMIT 0")
        conn.execute("INSERT INTO raw.customers SELECT * FROM df")


@asset
def raw_orders(duckdb: DuckDBResource) -> None:
    """Ingest raw orders data into the database."""
    data = {
        "order_id": [101, 102, 103, 104, 105, 106],
        "customer_id": [1, 2, 1, 3, 2, 4],
        "amount": [150.00, 250.00, 75.50, 320.00, 180.25, 95.00],
        "order_date": [
            "2024-06-01",
            "2024-06-02",
            "2024-06-03",
            "2024-06-04",
            "2024-06-05",
            "2024-06-06",
        ],
    }
    df = pd.DataFrame(data)

    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS raw")
        conn.execute("CREATE TABLE IF NOT EXISTS raw.orders AS SELECT * FROM df LIMIT 0")
        conn.execute("INSERT INTO raw.orders SELECT * FROM df")


@asset
def cleaned_customers(raw_customers: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize customer data."""
    df = raw_customers.copy()
    df["name"] = df["name"].str.strip().str.title()
    df["email"] = df["email"].str.lower()
    df["signup_date"] = pd.to_datetime(df["signup_date"])
    return df


@asset
def cleaned_orders(raw_orders: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize orders data."""
    df = raw_orders.copy()
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["amount"] = df["amount"].round(2)
    return df


@asset
def customer_orders(
    cleaned_customers: pd.DataFrame, cleaned_orders: pd.DataFrame, duckdb: DuckDBResource
) -> None:
    """Create enriched customer orders view with customer details."""
    merged = cleaned_orders.merge(cleaned_customers, on="customer_id", how="left")

    with duckdb.get_connection() as conn:
        conn.execute("CREATE SCHEMA IF NOT EXISTS analytics")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS analytics.customer_orders AS SELECT * FROM merged LIMIT 0"
        )
        conn.execute("INSERT INTO analytics.customer_orders SELECT * FROM merged")


@asset
def order_summary(duckdb: DuckDBResource) -> pd.DataFrame:
    """Calculate order summary statistics."""
    with duckdb.get_connection() as conn:
        result = conn.execute(
            """
            SELECT
                customer_id,
                name,
                COUNT(*) as total_orders,
                SUM(amount) as total_spent,
                AVG(amount) as avg_order_value
            FROM analytics.customer_orders
            GROUP BY customer_id, name
            ORDER BY total_spent DESC
            """
        ).fetch_df()
    return result
