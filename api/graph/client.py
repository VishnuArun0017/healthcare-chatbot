from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()


class Neo4jClient:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD", "testpass")
        self.database = os.getenv("NEO4J_DATABASE")
        self.trust_all = os.getenv("NEO4J_TRUST_ALL_CERTS", "false").lower() in {"1", "true", "yes"}
        self.driver = None
    
    def connect(self):
        """Connect to Neo4j database"""
        try:
            uri = self.uri
            if self.trust_all:
                uri = (
                    uri.replace("neo4j+s://", "neo4j+ssc://", 1)
                    .replace("bolt+s://", "bolt+ssc://", 1)
                )

            self.driver = GraphDatabase.driver(
                uri,
                auth=(self.user, self.password)
            )
            # Test connection
            session_args = {}
            if self.database:
                session_args["database"] = self.database

            with self.driver.session(**session_args) as session:
                result = session.run("RETURN 1 AS test")
                result.single()
            print(f"[OK] Connected to Neo4j at {uri}")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to connect to Neo4j: {e}")
            return False
    
    def close(self):
        """Close the connection"""
        if self.driver:
            self.driver.close()
    
    def run_cypher(self, query: str, params: dict = None):
        """
        Execute a Cypher query
        
        Args:
            query: Cypher query string
            params: Query parameters
            
        Returns:
            List of records
        """
        if not self.driver:
            raise Exception("Not connected to Neo4j. Call connect() first.")
        
        session_args = {}
        if self.database:
            session_args["database"] = self.database

        with self.driver.session(**session_args) as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]


# Global client instance
neo4j_client = Neo4jClient()


def run_cypher(query: str, params: dict = None):
    """Helper function to run Cypher queries"""
    return neo4j_client.run_cypher(query, params)