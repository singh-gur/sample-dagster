# Using Trino with Iceberg for Asset Storage

This Dagster pipeline uses your external Trino server with Iceberg tables for asset storage.

## Configuration

### 1. Set Environment Variables

Create a `.env` file or set these environment variables:

```bash
# Trino Connection
TRINO_HOST=your-trino-server.example.com
TRINO_PORT=8080
TRINO_USER=your-username
TRINO_CATALOG=iceberg
TRINO_SCHEMA=dagster_assets

# Iceberg Warehouse (optional - depends on your Trino setup)
ICEBERG_WAREHOUSE_PATH=s3://your-bucket/warehouse
```

Copy the example file to get started:
```bash
cp .env.example .env
# Edit .env with your Trino server details
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Run Dagster

```bash
dagster dev
```

## How It Works

The `TrinoIOManager` automatically:
- Converts Pandas DataFrames to Iceberg tables in Trino
- Creates tables with schema inferred from DataFrame dtypes
- Stores data in Parquet format
- Loads tables back as Pandas DataFrames for downstream assets

### Asset Flow

```python
@asset(compute_kind="trino")
def raw_sales_data(context) -> pd.DataFrame:
    df = pd.DataFrame(...)
    return df  # Stored as Iceberg table: iceberg.dagster_assets.raw_sales_data

@asset(compute_kind="trino")
def cleaned_sales_data(context, raw_sales_data: pd.DataFrame) -> pd.DataFrame:
    # raw_sales_data loaded from Iceberg table
    cleaned = raw_sales_data.copy()
    # ... processing ...
    return cleaned  # Stored as Iceberg table: iceberg.dagster_assets.cleaned_sales_data
```

## Table Naming

Tables are created using the asset key:
- Asset: `raw_sales_data` → Table: `iceberg.dagster_assets.raw_sales_data`
- Asset: `sales_metrics` → Table: `iceberg.dagster_assets.sales_metrics`

## Querying Your Data

You can query the Iceberg tables directly from Trino:

```sql
-- Connect to your Trino server
USE iceberg.dagster_assets;

-- List all asset tables
SHOW TABLES;

-- Query asset data
SELECT * FROM raw_sales_data LIMIT 10;
SELECT * FROM sales_metrics;
```

## Data Type Mapping

The IO Manager maps Pandas dtypes to Trino types:

| Pandas Type | Trino Type |
|-------------|------------|
| `int*` | `BIGINT` |
| `float*` | `DOUBLE` |
| `bool` | `BOOLEAN` |
| `datetime*` | `TIMESTAMP` |
| `date` | `DATE` |
| Others | `VARCHAR` |

## Customizing the IO Manager

You can customize the IO Manager in `src/sample_dagster/definitions.py`:

```python
from sample_dagster.defs.io_managers import TrinoIOManager

defs = Definitions(
    resources={
        "io_manager": TrinoIOManager(
            host="custom-host.example.com",
            port=8080,
            user="custom-user",
            catalog="my_catalog",
            schema="my_schema",
        )
    }
)
```

## Troubleshooting

### Connection Issues

If you can't connect to Trino:
1. Verify your Trino server is accessible
2. Check firewall rules allow connections on the Trino port
3. Verify credentials and catalog/schema exist

### Schema Permissions

The IO Manager needs permissions to:
- Create schemas (if `dagster_assets` doesn't exist)
- Create tables
- Insert data
- Query tables

Ensure your Trino user has these permissions on the Iceberg catalog.

### Table Already Exists

The IO Manager drops and recreates tables on each materialization. If you need to preserve data, modify the `handle_output` method in `src/sample_dagster/defs/io_managers/trino_io_manager.py`.

## Implementation Details

The IO Manager is located at:
- `src/sample_dagster/defs/io_managers/trino_io_manager.py`

Configuration constants are in:
- `src/sample_dagster/defs/constants.py`

All assets use `compute_kind="trino"` to indicate they use Trino storage.
