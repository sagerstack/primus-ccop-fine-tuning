"""Shared Neo4j driver helper for ontology_v2 scripts.

Thin wrapper over the project settings so every script connects the same way
the live graph nodes do (see rag/retrieval/nodes/compliance_gate_retrieval.py).
"""
from contextlib import contextmanager
from typing import Any, Dict, Iterator, List

from infrastructure.config.settings import get_settings


@contextmanager
def session() -> Iterator[Any]:
    import neo4j

    settings = get_settings()
    driver = neo4j.GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        with driver.session(database=settings.neo4j_database) as s:
            yield s
    finally:
        driver.close()


def query(cypher: str, **params: Any) -> List[Dict[str, Any]]:
    with session() as s:
        return [dict(r) for r in s.run(cypher, **params)]
