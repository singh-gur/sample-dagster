"""Trino IO Manager that stores data as Iceberg tables.

This IO Manager handles reading and writing Pandas DataFrames to Trino,
with data stored as Iceberg tables behind the scenes.
"""

import re
from typing import Any

import pandas as pd
import trino
from dagster import (
    ConfigurableIOManager,
    InputContext,
    OutputContext,
)
from dagster import (
    _check as check,
)
from trino.dbapi import Connection

from ..constants import (
    TRINO_CATALOG,
    TRINO_HOST,
    TRINO_PORT,
    TRINO_SCHEMA,
    TRINO_USER,
)


class TrinoIOManager(ConfigurableIOManager):
    """IO Manager for storing Dagster assets as Iceberg tables in Trino.

    This IO Manager:
    - Accepts Pandas DataFrames as outputs from assets
    - Stores them as Iceberg tables in Trino
    - Retrieves them as Pandas DataFrames for downstream assets
    - Automatically creates schemas if they don't exist
    - Uses asset keys to determine table names

    Configuration:
        host: Trino coordinator host (default: from TRINO_HOST env var)
        port: Trino coordinator port (default: from TRINO_PORT env var)
        user: Trino user (default: from TRINO_USER env var)
        catalog: Trino catalog name (default: from TRINO_CATALOG env var)
        schema: Default schema for tables (default: from TRINO_SCHEMA env var)
    """

    host: str = TRINO_HOST
    port: int = TRINO_PORT
    user: str = TRINO_USER
    catalog: str = TRINO_CATALOG
    schema: str = TRINO_SCHEMA

    def _get_connection(self) -> Connection:
        """Create a Trino database connection.

        Returns:
            Active Trino connection.
        """
        return trino.dbapi.connect(
            host=self.host,
            port=self.port,
            user=self.user,
            catalog=self.catalog,
            schema=self.schema,
        )

    def _get_table_name(self, context: OutputContext | InputContext) -> str:
        """Generate table name from asset key.

        Args:
            context: Dagster execution context containing asset metadata.

        Returns:
            Sanitized table name derived from asset key.
        """
        # Use asset key to generate table name
        # Convert asset key path to table name (e.g., ["sales", "metrics"] -> "sales_metrics")
        if context.asset_key:
            table_name = "_".join(context.asset_key.path)
        else:
            # Fallback to output/input name
            table_name = context.name

        # Sanitize table name (remove special characters, lowercase)
        table_name = re.sub(r"[^a-zA-Z0-9_]", "_", table_name).lower()

        return table_name

    def _ensure_schema_exists(self, conn: Connection) -> None:
        """Create schema if it doesn't exist.

        Args:
            conn: Active Trino connection.
        """
        cursor = conn.cursor()
        try:
            # Check if schema exists
            cursor.execute(
                f"CREATE SCHEMA IF NOT EXISTS {self.catalog}.{self.schema} "
                "WITH (location = 's3a://warehouse/')"
            )
        finally:
            cursor.close()

    def _pandas_dtype_to_trino(self, dtype: Any) -> str:
        """Convert Pandas dtype to Trino SQL type.

        Args:
            dtype: Pandas column dtype.

        Returns:
            Corresponding Trino SQL type string.
        """
        dtype_str = str(dtype)

        if "int" in dtype_str:
            return "BIGINT"
        elif "float" in dtype_str:
            return "DOUBLE"
        elif "bool" in dtype_str:
            return "BOOLEAN"
        elif "datetime" in dtype_str:
            return "TIMESTAMP"
        elif "date" in dtype_str:
            return "DATE"
        else:
            return "VARCHAR"

    def _create_table_from_dataframe(
        self, conn: Connection, table_name: str, df: pd.DataFrame
    ) -> None:
        """Create Iceberg table with schema inferred from DataFrame.

        Args:
            conn: Active Trino connection.
            table_name: Name of the table to create.
            df: DataFrame to infer schema from.
        """
        cursor = conn.cursor()
        try:
            # Generate column definitions
            columns = []
            for col_name, dtype in df.dtypes.items():
                trino_type = self._pandas_dtype_to_trino(dtype)
                # Sanitize column name
                safe_col_name = re.sub(r"[^a-zA-Z0-9_]", "_", str(col_name))
                columns.append(f"{safe_col_name} {trino_type}")

            columns_sql = ", ".join(columns)

            # Create Iceberg table
            create_sql = f"""
                CREATE TABLE IF NOT EXISTS {self.catalog}.{self.schema}.{table_name} (
                    {columns_sql}
                )
                WITH (
                    format = 'PARQUET'
                )
            """

            cursor.execute(create_sql)
        finally:
            cursor.close()

    def handle_output(self, context: OutputContext, obj: pd.DataFrame) -> None:
        """Store a Pandas DataFrame as an Iceberg table in Trino.

        Args:
            context: Dagster output context with asset metadata.
            obj: Pandas DataFrame to store.
        """
        check.inst_param(obj, "obj", pd.DataFrame)

        table_name = self._get_table_name(context)
        conn = self._get_connection()

        try:
            # Ensure schema exists
            self._ensure_schema_exists(conn)

            # Drop existing table if it exists (for simplicity - could be optimized)
            cursor = conn.cursor()
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {self.catalog}.{self.schema}.{table_name}")
            finally:
                cursor.close()

            # Create table with proper schema
            self._create_table_from_dataframe(conn, table_name, obj)

            # Insert data in batches
            if not obj.empty:
                # Sanitize column names to match table
                df_copy = obj.copy()
                df_copy.columns = [
                    re.sub(r"[^a-zA-Z0-9_]", "_", str(col)) for col in df_copy.columns
                ]

                # Convert DataFrame to list of tuples for insertion
                # Handle None/NaN values properly
                rows = []
                for _, row in df_copy.iterrows():
                    row_values = []
                    for val in row:
                        if pd.isna(val):
                            row_values.append(None)
                        elif isinstance(val, pd.Timestamp):
                            row_values.append(val.to_pydatetime())
                        else:
                            row_values.append(val)
                    rows.append(tuple(row_values))

                # Prepare INSERT statement
                columns_list = ", ".join(df_copy.columns)
                placeholders = ", ".join(["?" for _ in df_copy.columns])
                insert_sql = (
                    f"INSERT INTO {self.catalog}.{self.schema}.{table_name} "
                    f"({columns_list}) VALUES ({placeholders})"
                )

                # Execute batch insert
                cursor = conn.cursor()
                try:
                    cursor.executemany(insert_sql, rows)
                finally:
                    cursor.close()

            context.log.info(
                f"Stored {len(obj)} rows in Iceberg table: "
                f"{self.catalog}.{self.schema}.{table_name}"
            )

            # Add metadata
            context.add_output_metadata(
                {
                    "table": f"{self.catalog}.{self.schema}.{table_name}",
                    "row_count": len(obj),
                    "columns": list(obj.columns),
                }
            )

        finally:
            conn.close()

    def load_input(self, context: InputContext) -> pd.DataFrame:
        """Load an Iceberg table from Trino as a Pandas DataFrame.

        Args:
            context: Dagster input context with asset metadata.

        Returns:
            Pandas DataFrame containing the table data.
        """
        table_name = self._get_table_name(context)
        conn = self._get_connection()

        try:
            # Query the entire table
            query = f"SELECT * FROM {self.catalog}.{self.schema}.{table_name}"

            cursor = conn.cursor()
            try:
                cursor.execute(query)
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()

                df = pd.DataFrame(rows, columns=columns)

                context.log.info(
                    f"Loaded {len(df)} rows from Iceberg table: "
                    f"{self.catalog}.{self.schema}.{table_name}"
                )

                return df

            finally:
                cursor.close()

        finally:
            conn.close()
