"""Raw sales data ingestion asset.

This asset ingests raw sales transactions from a simulated source
and stores them in the data warehouse for further processing.
"""

import pandas as pd
from dagster import AssetExecutionContext, asset


@asset(
    deps=[],
    compute_kind="pandas",
)
def raw_sales_data(context: AssetExecutionContext) -> pd.DataFrame:
    """Ingest raw sales transactions from simulated source.

    This asset generates sample sales data that mimics what might come
    from an external API or database. In production, this would connect
    to the actual data source.

    Returns:
        DataFrame containing raw sales transactions with columns:
        - transaction_id: Unique identifier for each transaction
        - customer_id: Customer who made the purchase
        - product_id: Product that was purchased
        - quantity: Number of items purchased
        - unit_price: Price per item
        - transaction_date: When the transaction occurred
        - region: Geographic region of the sale
    """
    # Simulate raw data with some realistic characteristics
    from datetime import datetime, timedelta

    import numpy as np

    np.random.seed(42)  # Reproducible for testing

    n_transactions = 1000
    now = datetime.now()

    # Generate raw sales data
    data = {
        "transaction_id": [f"TXN-{i:06d}" for i in range(n_transactions)],
        "customer_id": [f"CUST-{np.random.randint(1, 201):03d}" for _ in range(n_transactions)],
        "product_id": [f"PROD-{np.random.randint(1, 51):03d}" for _ in range(n_transactions)],
        "quantity": np.random.randint(1, 10, size=n_transactions),
        "unit_price": np.round(np.random.uniform(10, 500, size=n_transactions), 2),
        "transaction_date": [
            (now - timedelta(days=np.random.randint(0, 90), hours=np.random.randint(0, 24)))
            for _ in range(n_transactions)
        ],
        "region": np.random.choice(
            ["North", "South", "East", "West", "Central"], size=n_transactions
        ),
    }

    df = pd.DataFrame(data)

    # Add some data quality issues that will be cleaned in the next step
    # Introduce missing values (simulating real-world data issues)
    mask = np.random.random(n_transactions) < 0.05  # 5% missing values
    df.loc[mask, "customer_id"] = None

    # Introduce some invalid prices (negative values)
    mask = np.random.random(n_transactions) < 0.02  # 2% invalid
    df.loc[mask, "unit_price"] = -df.loc[mask, "unit_price"]

    # Add some duplicate transactions
    duplicate_indices = np.random.choice(n_transactions, size=50, replace=False)
    df = pd.concat([df, df.iloc[duplicate_indices]], ignore_index=True)

    context.log.info(f"Ingested {len(df)} raw sales transactions")
    context.add_output_metadata(
        {"row_count": len(df), "columns": list(df.columns), "duplicate_count": 50}
    )

    return df


@asset(
    deps=["raw_sales_data"],
    compute_kind="pandas",
)
def raw_customers_data(context: AssetExecutionContext) -> pd.DataFrame:
    """Ingest raw customer reference data.

    Returns:
        DataFrame containing customer information with columns:
        - customer_id: Unique customer identifier
        - customer_name: Customer's full name
        - email: Customer email address
        - signup_date: When customer registered
        - tier: Customer loyalty tier (Bronze, Silver, Gold)
    """
    from datetime import datetime, timedelta

    import numpy as np

    np.random.seed(123)

    n_customers = 200
    now = datetime.now()

    tiers = ["Bronze", "Silver", "Gold"]
    tier_weights = [0.5, 0.35, 0.15]  # Most customers are Bronze

    data = {
        "customer_id": [f"CUST-{i:03d}" for i in range(1, n_customers + 1)],
        "customer_name": [f"Customer {i}" for i in range(1, n_customers + 1)],
        "email": [f"customer{i}@example.com" for i in range(1, n_customers + 1)],
        "signup_date": [
            now - timedelta(days=np.random.randint(1, 365 * 3)) for _ in range(n_customers)
        ],
        "tier": np.random.choice(tiers, size=n_customers, p=tier_weights),
    }

    df = pd.DataFrame(data)

    # Remove a few customers to test join handling
    df = df.iloc[np.random.choice(n_customers, size=n_customers - 5, replace=False)]

    context.log.info(f"Ingested {len(df)} customer records")
    context.add_output_metadata({"row_count": len(df)})

    return df
