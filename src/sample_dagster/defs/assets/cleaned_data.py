"""Data cleaning and validation asset.

This asset takes raw sales data, cleans it, validates it,
and produces a high-quality dataset ready for analysis.
"""

import pandas as pd
from dagster import AssetExecutionContext, asset


@asset(
    deps=["raw_sales_data"],
    compute_kind="pandas",
)
def cleaned_sales_data(
    context: AssetExecutionContext,
    raw_sales_data: pd.DataFrame,
) -> pd.DataFrame:
    """Clean and validate raw sales transactions.

    This asset performs the following transformations:
    1. Removes duplicate transactions
    2. Fills missing customer IDs with a placeholder
    3. Removes or corrects invalid values (negative prices)
    4. Standardizes data types
    5. Adds derived columns for analysis

    Args:
        context: The asset execution context.
        raw_sales_data: The raw sales data from upstream asset.

    Returns:
        Cleaned DataFrame ready for analysis.
    """
    df = raw_sales_data.copy()

    initial_count = len(df)

    # Step 1: Remove duplicate transactions
    df = df.drop_duplicates(subset=["transaction_id"], keep="first")
    duplicates_removed = initial_count - len(df)

    # Step 2: Handle missing customer IDs
    missing_customers = df["customer_id"].isna().sum()
    df["customer_id"] = df["customer_id"].fillna("UNKNOWN")

    # Step 3: Fix invalid prices (remove negative values)
    invalid_prices = (df["unit_price"] < 0).sum()
    df = df[df["unit_price"] >= 0]
    invalid_prices = initial_count - duplicates_removed - missing_customers - len(df)

    # Step 4: Standardize data types
    df["transaction_date"] = pd.to_datetime(df["transaction_date"])
    df["quantity"] = df["quantity"].astype(int)
    df["unit_price"] = df["unit_price"].astype(float)

    # Step 5: Add derived columns
    df["total_amount"] = df["quantity"] * df["unit_price"]
    df["transaction_date_only"] = df["transaction_date"].dt.date
    df["hour_of_day"] = df["transaction_date"].dt.hour
    df["day_of_week"] = df["transaction_date"].dt.day_name()

    final_count = len(df)

    context.log.info(
        f"Cleaned sales data: {initial_count} -> {final_count} rows "
        f"({duplicates_removed} duplicates, {invalid_prices} invalid prices removed)"
    )
    context.add_output_metadata(
        {
            "initial_rows": int(initial_count),
            "final_rows": int(final_count),
            "duplicates_removed": int(duplicates_removed),
            "missing_values_filled": int(missing_customers),
            "invalid_prices_removed": int(invalid_prices),
            "total_revenue": float(df["total_amount"].sum()),
            "avg_transaction_value": float(df["total_amount"].mean()),
        }
    )

    return df
