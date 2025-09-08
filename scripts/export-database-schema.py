#!/usr/bin/env python3
"""
Database Schema Documentation Generator
Generates comprehensive schema documentation for AI assistant reference.
"""
import json
import os
import sys
from typing import Any, Dict, List

import yaml

try:
    from sqlalchemy import create_engine, inspect, text
except ImportError:
    print("Missing dependencies. Install with: pip install pymysql sqlalchemy")
    sys.exit(1)


class DatabaseSchemaExporter:
    """Export database schema and sample data for AI reference."""

    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self.inspector = inspect(self.engine)

    def get_table_schema(self, table_name: str) -> Dict[str, Any]:
        """Get complete schema information for a table."""
        columns = self.inspector.get_columns(table_name)
        primary_keys = self.inspector.get_pk_constraint(table_name)
        foreign_keys = self.inspector.get_foreign_keys(table_name)
        indexes = self.inspector.get_indexes(table_name)

        return {
            "name": table_name,
            "columns": [
                {
                    "name": col["name"],
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "default": col["default"],
                    "primary_key": col["name"]
                    in primary_keys.get("constrained_columns", []),
                }
                for col in columns
            ],
            "primary_keys": primary_keys.get("constrained_columns", []),
            "foreign_keys": [
                {
                    "columns": fk["constrained_columns"],
                    "references_table": fk["referred_table"],
                    "references_columns": fk["referred_columns"],
                }
                for fk in foreign_keys
            ],
            "indexes": [
                {
                    "name": idx["name"],
                    "columns": idx["column_names"],
                    "unique": idx["unique"],
                }
                for idx in indexes
            ],
        }

    def get_sample_data(self, table_name: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT * FROM `{table_name}` LIMIT {limit}")
                )
                return [dict(row._mapping) for row in result]
        except Exception as e:
            print(f"Warning: Could not fetch sample data from {table_name}: {e}")
            return []

    def get_table_count(self, table_name: str) -> int:
        """Get total row count for a table."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text(f"SELECT COUNT(*) as count FROM `{table_name}`")
                )
                return result.fetchone()[0]
        except Exception as e:
            print(f"Warning: Could not count rows in {table_name}: {e}")
            return 0

    def export_complete_schema(self, output_dir: str = "docs/database"):
        """Export complete database schema documentation."""
        from datetime import datetime

        os.makedirs(output_dir, exist_ok=True)

        # Get all tables
        table_names = self.inspector.get_table_names()

        # Generate comprehensive documentation
        database_info = {
            "database_name": "trigpoin_trigs",
            "export_timestamp": str(datetime.now()),
            "total_tables": len(table_names),
            "tables": {},
        }

        for table_name in table_names:
            print(f"Processing table: {table_name}")

            schema = self.get_table_schema(table_name)
            sample_data = self.get_sample_data(table_name, 10)
            row_count = self.get_table_count(table_name)

            database_info["tables"][table_name] = {
                "schema": schema,
                "row_count": row_count,
                "sample_data": sample_data,
            }

        # Export as JSON (for AI assistant)
        with open(f"{output_dir}/schema_complete.json", "w") as f:
            json.dump(database_info, f, indent=2, default=str)

        # Export as YAML (human readable)
        with open(f"{output_dir}/schema_complete.yaml", "w") as f:
            yaml.dump(database_info, f, default_flow_style=False)

        # Generate markdown documentation
        self.generate_markdown_docs(database_info, output_dir)

        print(f"\n✅ Schema documentation exported to: {output_dir}")
        print(f"📊 Database summary: {len(table_names)} tables")

        return database_info

    def generate_markdown_docs(self, database_info: Dict, output_dir: str):
        """Generate human-readable markdown documentation."""
        md_content = [
            "# Database Schema Documentation",
            "",
            f"**Database:** {database_info['database_name']}",
            f"**Export Date:** {database_info['export_timestamp']}",
            f"**Total Tables:** {database_info['total_tables']}",
            "",
            "## Table Overview",
            "",
        ]

        # Table summary
        for table_name, table_info in database_info["tables"].items():
            row_count = table_info["row_count"]
            column_count = len(table_info["schema"]["columns"])
            md_content.extend(
                [f"- **{table_name}**: {row_count:,} rows, {column_count} columns"]
            )

        md_content.extend(["", "## Detailed Table Schemas", ""])

        # Detailed schemas
        for table_name, table_info in database_info["tables"].items():
            schema = table_info["schema"]
            sample_data = table_info["sample_data"]

            md_content.extend(
                [
                    f"### {table_name}",
                    "",
                    f"**Rows:** {table_info['row_count']:,}",
                    "",
                    "#### Columns",
                    "| Column | Type | Nullable | Default | Primary Key |",
                    "|--------|------|----------|---------|-------------|",
                ]
            )

            for col in schema["columns"]:
                pk_indicator = "✅" if col["primary_key"] else ""
                nullable = "Yes" if col["nullable"] else "No"
                default = str(col["default"]) if col["default"] is not None else ""
                md_content.append(
                    f"| {col['name']} | {col['type']} | {nullable} | {default} | {pk_indicator} |"
                )

            # Foreign keys
            if schema["foreign_keys"]:
                md_content.extend(
                    [
                        "",
                        "#### Foreign Keys",
                        "| Column(s) | References |",
                        "|-----------|------------|",
                    ]
                )
                for fk in schema["foreign_keys"]:
                    cols = ", ".join(fk["columns"])
                    refs = f"{fk['references_table']}.{', '.join(fk['references_columns'])}"
                    md_content.append(f"| {cols} | {refs} |")

            # Sample data
            if sample_data:
                md_content.extend(["", "#### Sample Data", "```json"])
                md_content.append(json.dumps(sample_data[:3], indent=2, default=str))
                md_content.extend(["```", ""])

        with open(f"{output_dir}/schema_documentation.md", "w") as f:
            f.write("\n".join(md_content))


def main():
    """Main execution function."""

    # Get database URL from environment or construct it
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        # Construct from individual components
        host = os.getenv(
            "DB_HOST", "fastapi-staging-db.cykrokraghk3.us-west-2.rds.amazonaws.com"
        )
        port = os.getenv("DB_PORT", "3306")
        user = os.getenv("DB_USER", "fastapi_user")
        password = os.getenv("DB_PASSWORD")
        database = os.getenv("DB_NAME", "trigpoin_trigs")

        if not password:
            password = input("Enter database password: ")

        database_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}"

    print("🔍 Connecting to database...")
    exporter = DatabaseSchemaExporter(database_url)

    print("📊 Exporting schema documentation...")
    exporter.export_complete_schema()


if __name__ == "__main__":
    main()
