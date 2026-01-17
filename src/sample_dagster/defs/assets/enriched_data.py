"""Data enrichment asset.

This asset enriches cleaned sales data with customer information
to provide a complete view of each transaction.
"""

import pandas as pd
from dagster import AssetExecutionContext, asset


@asset(
    deps=["cleaned_sales_data", "raw_customers_data"],
    compute_kind="pandas",
)
def enriched_sales_data(
    context: AssetExecutionContext,
    cleaned_sales_data: pd.DataFrame,
    raw_customers_data: pd.DataFrame,
) -> pd.DataFrame:
    """Enrich sales data with customer information.

    This asset performs a left join to add customer details to each
    sales transaction while preserving all sales records.

    Args:
        context: The asset execution context.
        cleaned_sales_data: The cleaned sales data.
        raw_customers_data: Customer reference data.

    Returns:
        Enriched DataFrame with customer details joined to transactions.
    """
    sales_df = cleaned_sales_data.copy()
    customers_df = raw_customers_data.copy()

    # Perform left join to enrich sales with customer data
    enriched_df = sales_df.merge(
        customers_df,
        on="customer_id",
        how="left",
        suffixes=("_sale", "_customer"),
    )

    # Fill missing customer info
    missing_customers = enriched_df["customer_name"].isna().sum()
    enriched_df["customer_name"] = enriched_df["customer_name"].fillna("Unknown Customer")
    enriched_df["email"] = enriched_df["email"].fillna("unknown@example.com")
    enriched_df["tier"] = enriched_df["tier"].fillna("Bronze")
    enriched_df["signup_date"] = enriched_df["signup_date"].fillna(enriched_df["transaction_date"])

    # Add customer tenure at time of transaction (in days)
    enriched_df["customer_tenure_days"] = (
        enriched_df["transaction_date"] - enriched_df["signup_date"]
    ).dt.days

    # Calculate days since signup (should be positive for existing customers)
    enriched_df["days_since_signup"] = (
        enriched_df["transaction_date"].dt.date - enriched_df["signup_date"].dt.date
    ).apply(lambda x: x.days)

    # Categorize customers by tenure
    def categorize_tenure(days: int) -> str:
        if days < 30:
            return "New"
        elif days < 365:
            return "Developing"
        elif days < 730:
            return "Established"
        else:
            return "Loyal"

    enriched_df["customer_category"] = enriched_df["days_since_signup"].apply(categorize_tenure)

    context.log.info(f"Enriched {len(enriched_df)} transactions with customer data")
    context.add_output_metadata(
        {
            "rows_enriched": int(len(enriched_df)),
            "missing_customers_filled": int(missing_customers),
            "unique_customers": int(enriched_df["customer_id"].nunique()),
            "tier_distribution": {
                k: int(v) for k, v in enriched_df["tier"].value_counts().to_dict().items()
            },
        }
    )

    return enriched_df
