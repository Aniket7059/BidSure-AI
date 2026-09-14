import os
import sqlite3
from sqlalchemy import create_engine, MetaData, text
from dotenv import load_dotenv

load_dotenv()

SQLITE_URL = "sqlite:///./bidsure.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

if not POSTGRES_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

print("=" * 60)
print("SQLite → PostgreSQL Data Migration")
print("=" * 60)

# ---------------------------------------------------------
# Create engines
# ---------------------------------------------------------

sqlite_engine = create_engine(SQLITE_URL)
postgres_engine = create_engine(POSTGRES_URL)

sqlite_meta = MetaData()
postgres_meta = MetaData()

sqlite_meta.reflect(bind=sqlite_engine)
postgres_meta.reflect(bind=postgres_engine)

# ---------------------------------------------------------
# Tables in dependency order
# ---------------------------------------------------------

tables = [
    "users",
    "bidders",
    "tenders",
    "bid_submissions",
    "tender_requirements",
    "bid_documents",
    "document_extractions",
    "verification_results",
    "compliance_checks",
    "compliance_assessments",
    "discrepancies",
    "procurement_decisions",
    "audit_logs",
]

# ---------------------------------------------------------
# Check tables
# ---------------------------------------------------------

print("\nChecking tables...")

for table_name in tables:
    if table_name not in sqlite_meta.tables:
        raise RuntimeError(f"Missing SQLite table: {table_name}")

    if table_name not in postgres_meta.tables:
        raise RuntimeError(f"Missing PostgreSQL table: {table_name}")

print("All required tables found.")

# ---------------------------------------------------------
# Migrate data
# ---------------------------------------------------------

with sqlite_engine.connect() as sqlite_conn, \
     postgres_engine.begin() as pg_conn:

    for table_name in tables:

        sqlite_table = sqlite_meta.tables[table_name]
        postgres_table = postgres_meta.tables[table_name]

        rows = sqlite_conn.execute(
            sqlite_table.select()
        ).mappings().all()

        print(f"\n{table_name}: {len(rows)} rows found")

        if not rows:
            print(f"  → Nothing to migrate")
            continue

        # -------------------------------------------------
        # Users:
        # The first two users were already seeded in
        # PostgreSQL, so don't insert them again.
        # -------------------------------------------------

        if table_name == "users":
            filtered_rows = []

            for row in rows:
                user_id = row["id"]

                if user_id in (1, 2):
                    existing = pg_conn.execute(
                        text(
                            "SELECT id, email FROM users WHERE id = :id"
                        ),
                        {"id": user_id},
                    ).fetchone()

                    if existing:
                        print(
                            f"  → Skipping existing user "
                            f"{row['email']} (ID {user_id})"
                        )
                        continue

                filtered_rows.append(dict(row))

            rows = filtered_rows

        if not rows:
            print("  → All rows already exist")
            continue

        # -------------------------------------------------
        # Insert rows
        # -------------------------------------------------

        for row in rows:
            pg_conn.execute(
                postgres_table.insert().values(**row)
            )

        print(f"  → Migrated {len(rows)} rows")

print("\n" + "=" * 60)
print("Data migration completed successfully.")
print("=" * 60)

# ---------------------------------------------------------
# Reset PostgreSQL sequences
# ---------------------------------------------------------

print("\nResetting PostgreSQL ID sequences...")

sequence_tables = [
    "users",
    "bidders",
    "tenders",
    "bid_submissions",
    "tender_requirements",
    "bid_documents",
    "document_extractions",
    "verification_results",
    "compliance_checks",
    "compliance_assessments",
    "discrepancies",
    "procurement_decisions",
    "audit_logs",
]

with postgres_engine.begin() as conn:

    for table_name in sequence_tables:

        result = conn.execute(
            text(
                """
                SELECT pg_get_serial_sequence(:table_name, 'id')
                """
            ),
            {"table_name": table_name},
        ).scalar()

        if result:
            conn.execute(
                text(
                    f"""
                    SELECT setval(
                        '{result}',
                        COALESCE((SELECT MAX(id) FROM "{table_name}"), 1),
                        (SELECT COUNT(*) > 0 FROM "{table_name}")
                    )
                    """
                )
            )

            print(f"  → Reset sequence for {table_name}")

print("\n" + "=" * 60)
print("Migration finished.")
print("=" * 60)