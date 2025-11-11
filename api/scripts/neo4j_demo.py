"""
Neo4j Aura connection smoke-test.

Follows the steps from the official Aura quick start:
1. Verify connectivity.
2. Create sample nodes/relationships.
3. Query them back.
4. Clean up the driver/session.
"""

from __future__ import annotations

from neo4j import GraphDatabase
from pathlib import Path
from typing import Tuple
import os
import sys

from dotenv import load_dotenv


def load_credentials() -> Tuple[str, Tuple[str, str]]:
    """Load URI and auth tuple from .env."""
    project_root = Path(__file__).resolve().parents[1]
    env_path = project_root / ".env"
    load_dotenv(env_path)

    uri = os.getenv("NEO4J_URI")
    trust_all = os.getenv("NEO4J_TRUST_ALL_CERTS", "false").lower() in {"1", "true", "yes"}

    if trust_all:
        uri = uri.replace("neo4j+s://", "neo4j+ssc://", 1).replace("bolt+s://", "bolt+ssc://", 1)
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        raise RuntimeError("NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD must be set in .env.")

    return uri, (user, password)


def main() -> None:
    uri, auth = load_credentials()
    print(f"Connecting to {uri} as {auth[0]} ...")

    driver = GraphDatabase.driver(uri, auth=auth)

    try:
        driver.verify_connectivity()
        print("Connectivity check passed.")

        summary = driver.execute_query(
            """
            CREATE (a:Person {name: $name})
            CREATE (b:Person {name: $friend_name})
            CREATE (a)-[:KNOWS]->(b)
            """,
            name="Alice",
            friend_name="David",
            database_="neo4j",
        ).summary

        print(
            f"Created {summary.counters.nodes_created} nodes "
            f"in {summary.result_available_after} ms."
        )

        records, summary, _ = driver.execute_query(
            """
            MATCH (p:Person)-[:KNOWS]->(:Person)
            RETURN p.name AS name
            """,
            database_="neo4j",
        )

        print("Query results:")
        for record in records:
            print(f"  - {record['name']}")

        print(
            f"Query `{summary.query}` returned {len(records)} records "
            f"in {summary.result_available_after} ms."
        )

    finally:
        driver.close()
        print("Driver closed.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"[ERROR] {exc}")
        sys.exit(1)

