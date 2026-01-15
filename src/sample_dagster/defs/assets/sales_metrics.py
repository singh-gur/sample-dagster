"""Sales metrics aggregation asset.

This asset takes enriched sales data and produces aggregated
metrics and summaries for business analysis and reporting.
"""

import pandas as pd
from dagster import AssetExecutionContext, asset


@asset(
    deps=["enriched_sales_data"],
    compute_kind="pandas",
)
def sales_metrics(
    context: AssetExecutionContext,
    enriched_sales_data: pd.DataFrame,
) -> pd.DataFrame:
    """Generate aggregated sales metrics by various dimensions.

    This asset creates summary statistics and KPIs for business reporting,
    including:
    - Daily sales totals
    - Product performance rankings
    - Customer segment analysis
    - Regional performance comparisons

    Args:
        context: The asset execution context.
        enriched_sales_data: The enriched sales transactions.

    Returns:
        Summary metrics DataFrame ready for dashboards/reporting.
    """
    df = enriched_sales_data.copy()

    # Daily sales summary
    daily_sales = (
        df.groupby("transaction_date_only")
        .agg(
            total_revenue=("total_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            avg_order_value=("total_amount", "mean"),
            unique_customers=("customer_id", "nunique"),
        )
        .reset_index()
    )
    daily_sales["date"] = pd.to_datetime(daily_sales["transaction_date_only"])

    # Product performance
    product_performance = (
        df.groupby("product_id")
        .agg(
            total_quantity_sold=("quantity", "sum"),
            total_revenue=("total_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            avg_price=("unit_price", "mean"),
        )
        .reset_index()
    )
    product_performance["rank_by_revenue"] = product_performance["total_revenue"].rank(
        ascending=False
    )

    # Regional performance
    regional_performance = (
        df.groupby("region")
        .agg(
            total_revenue=("total_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            avg_order_value=("total_amount", "mean"),
            unique_customers=("customer_id", "nunique"),
        )
        .reset_index()
    )
    regional_performance["revenue_share"] = (
        regional_performance["total_revenue"] / regional_performance["total_revenue"].sum()
    )

    context.log.info(
        f"Generated sales metrics: {len(daily_sales)} days, "
        f"{len(product_performance)} products, "
        f"{len(regional_performance)} regions"
    )
    context.add_output_metadata(
        {
            "total_revenue": df["total_amount"].sum(),
            "total_transactions": len(df),
            "unique_customers": df["customer_id"].nunique(),
            "days_analyzed": len(daily_sales),
            "products_ranked": len(product_performance),
        }
    )

    # Return all metrics - in production, these might be separate assets
    # For simplicity, we return the daily sales as the primary output
    return daily_sales


@asset(
    deps=["enriched_sales_data"],
    compute_kind="pandas",
)
def product_performance(
    context: AssetExecutionContext,
    enriched_sales_data: pd.DataFrame,
) -> pd.DataFrame:
    """Generate product performance rankings.

    Args:
        context: The asset execution context.
        enriched_sales_data: The enriched sales transactions.

    Returns:
        Product performance rankings DataFrame.
    """
    df = enriched_sales_data.copy()

    product_performance = (
        df.groupby("product_id")
        .agg(
            total_quantity_sold=("quantity", "sum"),
            total_revenue=("total_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            avg_price=("unit_price", "mean"),
        )
        .reset_index()
    )
    product_performance["rank_by_revenue"] = product_performance["total_revenue"].rank(
        ascending=False
    )
    product_performance = product_performance.sort_values("rank_by_revenue")

    context.add_output_metadata(
        {
            "top_product": product_performance.iloc[0]["product_id"],
            "top_product_revenue": product_performance.iloc[0]["total_revenue"],
        }
    )

    return product_performance


@asset(
    deps=["enriched_sales_data"],
    compute_kind="pandas",
)
def customer_insights(
    context: AssetExecutionContext,
    enriched_sales_data: pd.DataFrame,
) -> pd.DataFrame:
    """Generate customer-level insights and segmentation.

    Args:
        context: The asset execution context.
        enriched_sales_data: The enriched sales transactions.

    Returns:
        Customer insights DataFrame with lifetime value and behavior metrics.
    """
    df = enriched_sales_data.copy()

    # Customer-level aggregation
    customer_insights = (
        df.groupby("customer_id")
        .agg(
            total_revenue=("total_amount", "sum"),
            transaction_count=("transaction_id", "count"),
            avg_order_value=("total_amount", "mean"),
            total_items=("quantity", "sum"),
            first_transaction=("transaction_date", "min"),
            last_transaction=("transaction_date", "max"),
            customer_tier=("tier", "first"),
            customer_category=("customer_category", "first"),
        )
        .reset_index()
    )

    # Calculate customer lifetime and metrics
    customer_insights["customer_lifetime_days"] = (
        customer_insights["last_transaction"] - customer_insights["first_transaction"]
    ).dt.days

    # Calculate purchase frequency
    customer_insights["purchase_frequency"] = customer_insights["transaction_count"] / (
        customer_insights["customer_lifetime_days"] + 1
    )  # +1 to avoid division by zero

    # Rank customers by value
    customer_insights["value_rank"] = customer_insights["total_revenue"].rank(ascending=False)

    context.log.info(f"Generated insights for {len(customer_insights)} customers")
    context.add_output_metadata(
        {
            "total_customers": len(customer_insights),
            "total_revenue": customer_insights["total_revenue"].sum(),
            "top_customer_value": customer_insights.iloc[0]["total_revenue"],
        }
    )

    return customer_insights
