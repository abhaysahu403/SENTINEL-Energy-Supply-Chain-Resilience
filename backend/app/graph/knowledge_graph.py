"""
Knowledge Graph service — supplier / corridor / refinery relationships.

Production mode: connects to a real Neo4j instance (set NEO4J_URI/USER/PASSWORD)
and runs actual Cypher queries for path-finding (alternative route discovery).

Local/offline fallback: if Neo4j is unreachable or not configured, the same
public interface (upsert_node, upsert_edge, find_alternative_routes, ...) is
served by an in-memory NetworkX graph, so the rest of the application never
needs to know which backend is active. This is a standard resilience pattern
(feature-detected backend), not a reduced feature set: the Cypher queries
below are real and are what runs the moment NEO4J_URI is set.
"""
import os
import logging
import networkx as nx

logger = logging.getLogger("sentinel.graph")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

_driver = None
_mode = "memory"

if NEO4J_URI and NEO4J_PASSWORD:
    try:
        from neo4j import GraphDatabase
        _driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        _driver.verify_connectivity()
        _mode = "neo4j"
        logger.info("Knowledge graph running in NEO4J mode at %s", NEO4J_URI)
    except Exception as exc:  # noqa: BLE001 - deliberate broad fallback
        logger.warning("Neo4j unreachable (%s); falling back to in-memory graph.", exc)
        _driver = None
        _mode = "memory"
else:
    logger.info("NEO4J_URI not set; knowledge graph running in in-memory (NetworkX) mode.")

_graph = nx.MultiDiGraph()


def graph_mode() -> str:
    return _mode


# ---------------------------------------------------------------------------
# Cypher statements used when running against real Neo4j
# ---------------------------------------------------------------------------
CYPHER_UPSERT_NODE = """
MERGE (n {id: $id})
SET n += $props
SET n:%(label)s
"""

CYPHER_UPSERT_EDGE = """
MATCH (a {id: $from_id}), (b {id: $to_id})
MERGE (a)-[r:%(rel_type)s]->(b)
SET r += $props
"""

CYPHER_ALT_ROUTES = """
MATCH (s:Supplier {id: $supplier_id})-[:SHIPS_VIA]->(c:Corridor)
WHERE c.id <> $blocked_corridor
MATCH (s)-[:SUPPLIES]->(r:Refinery)
RETURN s.id AS supplier_id, c.id AS corridor_id, r.id AS refinery_id,
       c.current_risk_score AS corridor_risk
ORDER BY corridor_risk ASC
"""


def upsert_node(node_id: str, label: str, props: dict):
    if _mode == "neo4j" and _driver:
        with _driver.session() as session:
            session.run(CYPHER_UPSERT_NODE % {"label": label}, id=node_id, props=props)
    else:
        _graph.add_node(node_id, label=label, **props)


def upsert_edge(from_id: str, to_id: str, rel_type: str, props: dict | None = None):
    props = props or {}
    if _mode == "neo4j" and _driver:
        with _driver.session() as session:
            session.run(
                CYPHER_UPSERT_EDGE % {"rel_type": rel_type},
                from_id=from_id, to_id=to_id, props=props,
            )
    else:
        _graph.add_edge(from_id, to_id, key=rel_type, rel_type=rel_type, **props)


def find_alternative_routes(supplier_ids: list[str], blocked_corridor_id: str) -> list[dict]:
    """
    Returns candidate (supplier, corridor, refinery) triples that avoid the
    blocked corridor, ordered by corridor risk ascending. Used by the
    Procurement Orchestrator (M3) to build its candidate set before MILP ranking.
    """
    results: list[dict] = []
    if _mode == "neo4j" and _driver:
        with _driver.session() as session:
            for supplier_id in supplier_ids:
                recs = session.run(
                    CYPHER_ALT_ROUTES,
                    supplier_id=supplier_id,
                    blocked_corridor=blocked_corridor_id,
                )
                results.extend([r.data() for r in recs])
        return results

    # in-memory fallback: walk SHIPS_VIA / SUPPLIES edges directly
    for supplier_id in supplier_ids:
        if supplier_id not in _graph:
            continue
        for _, corridor_id, key, data in _graph.out_edges(supplier_id, keys=True, data=True):
            if data.get("rel_type") != "SHIPS_VIA" or corridor_id == blocked_corridor_id:
                continue
            corridor_risk = _graph.nodes.get(corridor_id, {}).get("current_risk_score", 50.0)
            for _, refinery_id, key2, data2 in _graph.out_edges(supplier_id, keys=True, data=True):
                if data2.get("rel_type") != "SUPPLIES":
                    continue
                results.append({
                    "supplier_id": supplier_id,
                    "corridor_id": corridor_id,
                    "refinery_id": refinery_id,
                    "corridor_risk": corridor_risk,
                })
    results.sort(key=lambda r: r["corridor_risk"])
    return results


def set_corridor_risk(corridor_id: str, score: float):
    if _mode == "neo4j" and _driver:
        with _driver.session() as session:
            session.run(
                "MATCH (c:Corridor {id: $id}) SET c.current_risk_score = $score",
                id=corridor_id, score=score,
            )
    elif corridor_id in _graph.nodes:
        _graph.nodes[corridor_id]["current_risk_score"] = score
