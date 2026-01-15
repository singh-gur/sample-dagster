"""Assets for the sales data pipeline.

This module contains a multi-step data pipeline that:
1. Ingests raw sales and customer data
2. Cleans and validates the data
3. Enriches transactions with customer information
4. Generates aggregated metrics and insights
"""

from .cleaned_data import cleaned_sales_data
from .enriched_data import enriched_sales_data
from .raw_data import raw_customers_data, raw_sales_data
from .sales_metrics import customer_insights, product_performance, sales_metrics

__all__ = [
    "raw_sales_data",
    "raw_customers_data",
    "cleaned_sales_data",
    "enriched_sales_data",
    "sales_metrics",
    "product_performance",
    "customer_insights",
]
