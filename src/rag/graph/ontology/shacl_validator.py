"""
SHACL validation backstop for the ontology-grounded CCoP KG (Phase 10, D-13).

"Validation is the line between toy and production." Whatever slips past the
schema-constrained extraction prompt (D-07) is caught here STRUCTURALLY:

  1. Export the built graph LPG -> RDF (query Neo4j into an in-memory
     `rdflib.Graph`, mirroring `KGInspector`'s session-query style).
  2. Validate the data graph against the committed `shapes.ttl` (D-07
     canonical-name-required / junk-name-rejected constraints) via
     pure-Python `pyshacl.validate` — NOT n10s (unverified Neo4j 5.26
     compatibility, heavier operational surface — RESEARCH Pitfall 5 / Q5).
  3. QUARANTINE non-conforming facts: collect every violation (focusNode /
     resultPath / severity / message) into a `ValidationReport` and write it
     to `validation_report.json`. Facts are rejected + LOGGED SEPARATELY,
     NEVER silently deleted (D-13) — the graph is not mutated by validation.

The LPG -> RDF export and the `validate_rdf` core are PURE functions (no live
driver needed) so the constraint logic is unit-testable in memory; only the
top-level `validate()` orchestration touches Neo4j.

Threat model (T-10-08-02): the export Cypher is a static literal with no
interpolated values — no injection surface. (T-10-08-03): `shapes.ttl` is a
committed repo artifact parsed as trusted local SHACL, never user-supplied.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Optional, Union

import neo4j
from pyshacl import validate as pyshacl_validate
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, SH

logger = logging.getLogger(__name__)

# Base namespace for the LPG -> RDF export. Node URIs, type labels, property
# predicates and relationship predicates all live under this namespace, matching
# the `ccop:` prefix declared in shapes.ttl.
CCOP = Namespace("http://ccop.example/kg#")

# Committed SHACL shapes, resolved relative to this file so the path is correct
# regardless of the caller's working directory.
DEFAULT_SHAPES_PATH = Path(__file__).resolve().parent / "shapes.ttl"

# Default quarantine-report destination (D-13: reject + log separately).
DEFAULT_REPORT_PATH = Path(__file__).resolve().parent / "validation_report.json"

# Static LPG -> RDF export queries (T-10-08-02: no interpolated values).
_EXPORT_NODES_CYPHER = (
    "MATCH (n) "
    "RETURN elementId(n) AS id, labels(n) AS labels, properties(n) AS props"
)
_EXPORT_RELS_CYPHER = (
    "MATCH (a)-[r]->(b) "
    "RETURN elementId(a) AS source, elementId(b) AS target, type(r) AS rel_type"
)

PathLike = Union[str, Path]


@dataclass
class Violation:
    """One quarantined non-conforming fact (a SHACL validation result)."""

    focus_node: str
    result_path: Optional[str]
    severity: Optional[str]
    source_shape: Optional[str]
    value: Optional[str]
    message: Optional[str]


@dataclass
class ValidationReport:
    """
    Outcome of a SHACL validation pass (D-13 quarantine record).

    `conforms` is the SHACL `sh:conforms` flag; `violations` is the quarantined
    (reject + log) list — the data graph is never deleted from.
    """

    conforms: bool
    violations: list[Violation] = field(default_factory=list)
    results_text: str = ""

    @property
    def violation_count(self) -> int:
        return len(self.violations)

    @property
    def high_severity_count(self) -> int:
        """Count of `sh:Violation`-severity results (the build-gating ones)."""
        return sum(
            1
            for v in self.violations
            if v.severity and v.severity.endswith("Violation")
        )

    def severity_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self.violations:
            key = (v.severity or "Unknown").rsplit("#", 1)[-1]
            counts[key] = counts.get(key, 0) + 1
        return counts

    def shape_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for v in self.violations:
            key = (v.source_shape or "Unknown").rsplit("#", 1)[-1]
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> dict[str, Any]:
        return {
            "conforms": self.conforms,
            "violation_count": self.violation_count,
            "high_severity_count": self.high_severity_count,
            "severity_counts": self.severity_counts(),
            "shape_counts": self.shape_counts(),
            "violations": [asdict(v) for v in self.violations],
        }

    def write_json(self, path: PathLike = DEFAULT_REPORT_PATH) -> Path:
        """Quarantine the violations to disk (D-13 log separately)."""
        out = Path(path)
        out.write_text(json.dumps(self.to_dict(), indent=2, default=str))
        return out


def lpg_to_rdf(
    node_records: list[dict[str, Any]],
    rel_records: list[dict[str, Any]],
) -> Graph:
    """
    Map a Neo4j labelled-property graph into an in-memory `rdflib.Graph`.

    Pure function (no driver): each node becomes a URI under `CCOP`, every label
    a `rdf:type` triple, every property a literal triple, and every relationship
    a predicate triple. Structural neo4j-graphrag labels (Chunk/Document/
    __Entity__/__KGBuilder__) are exported too but carry no SHACL shape, so they
    are simply ignored by validation.
    """
    g = Graph()
    g.bind("ccop", CCOP)

    for record in node_records:
        node_uri = CCOP[str(record["id"])]
        for label in record.get("labels", []):
            g.add((node_uri, RDF.type, CCOP[label]))
        for key, value in (record.get("props") or {}).items():
            if value is None:
                continue
            g.add((node_uri, CCOP[key], Literal(value)))

    for record in rel_records:
        source_uri = CCOP[str(record["source"])]
        target_uri = CCOP[str(record["target"])]
        g.add((source_uri, CCOP[record["rel_type"]], target_uri))

    return g


class SHACLValidator:
    """
    Export-and-validate SHACL backstop (D-13).

    Constructed from a live `neo4j.Driver` for the `validate()` orchestration;
    `driver=None` is valid for exercising the pure `validate_rdf` / export
    helpers in unit tests.
    """

    def __init__(
        self,
        driver: Optional[neo4j.Driver] = None,
        database: str = "neo4j",
        shapes_path: PathLike = DEFAULT_SHAPES_PATH,
    ) -> None:
        self.driver = driver
        self.database = database
        self.shapes_path = Path(shapes_path)
        self._shapes_graph: Optional[Graph] = None

    # ------------------------------------------------------------------
    # Shapes
    # ------------------------------------------------------------------

    def load_shapes(self) -> Graph:
        """Parse (and cache) the committed shapes.ttl (trusted local artifact)."""
        if self._shapes_graph is None:
            shapes = Graph()
            shapes.parse(str(self.shapes_path), format="turtle")
            self._shapes_graph = shapes
        return self._shapes_graph

    # ------------------------------------------------------------------
    # Export (LPG -> RDF) — touches Neo4j
    # ------------------------------------------------------------------

    def _session(self):
        if self.driver is None:
            raise RuntimeError(
                "SHACLValidator has no Neo4j driver; use validate_rdf() for "
                "in-memory validation or construct with a driver for validate()."
            )
        return self.driver.session(database=self.database)

    def export_to_rdf(self) -> Graph:
        """Query the live graph and build the in-memory RDF data graph."""
        with self._session() as session:
            node_records = [
                {"id": r["id"], "labels": r["labels"], "props": dict(r["props"])}
                for r in session.run(_EXPORT_NODES_CYPHER)
            ]
            rel_records = [
                {
                    "source": r["source"],
                    "target": r["target"],
                    "rel_type": r["rel_type"],
                }
                for r in session.run(_EXPORT_RELS_CYPHER)
            ]
        return lpg_to_rdf(node_records, rel_records)

    # ------------------------------------------------------------------
    # Validation (pure) — no driver required
    # ------------------------------------------------------------------

    def validate_rdf(self, data_graph: Graph) -> ValidationReport:
        """
        Validate an in-memory data graph against the committed shapes.

        Pure: does not mutate `data_graph` (D-13 — quarantine, never delete).
        """
        conforms, results_graph, results_text = pyshacl_validate(
            data_graph,
            shacl_graph=self.load_shapes(),
            inference="none",
            abort_on_error=False,
            meta_shacl=False,
            advanced=True,
        )
        violations = self._parse_results(results_graph)
        return ValidationReport(
            conforms=conforms,
            violations=violations,
            results_text=results_text or "",
        )

    @staticmethod
    def _parse_results(results_graph: Graph) -> list[Violation]:
        """Iterate the SHACL Validation Report graph into quarantine records."""
        violations: list[Violation] = []
        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            focus = results_graph.value(result, SH.focusNode)
            path = results_graph.value(result, SH.resultPath)
            severity = results_graph.value(result, SH.resultSeverity)
            shape = results_graph.value(result, SH.sourceShape)
            value = results_graph.value(result, SH.value)
            message = results_graph.value(result, SH.resultMessage)
            violations.append(
                Violation(
                    focus_node=str(focus) if focus is not None else "",
                    result_path=str(path) if path is not None else None,
                    severity=str(severity) if severity is not None else None,
                    source_shape=_shape_label(shape),
                    value=str(value) if value is not None else None,
                    message=str(message) if message is not None else None,
                )
            )
        # Stable ordering for deterministic reports.
        violations.sort(key=lambda v: (v.focus_node, v.result_path or ""))
        return violations

    # ------------------------------------------------------------------
    # Orchestration (export -> validate -> quarantine) — touches Neo4j
    # ------------------------------------------------------------------

    def validate(
        self,
        report_path: Optional[PathLike] = DEFAULT_REPORT_PATH,
    ) -> ValidationReport:
        """
        Full backstop pass: export the live graph, validate, and QUARANTINE any
        violations to `report_path` (D-13). Returns the report. The graph is
        NEVER mutated — non-conforming facts are logged separately, not deleted.
        """
        data_graph = self.export_to_rdf()
        report = self.validate_rdf(data_graph)
        if report_path is not None and not report.conforms:
            written = report.write_json(report_path)
            logger.warning(
                "SHACL validation found %d violation(s); quarantined to %s "
                "(reject + log separately, D-13 — no facts deleted).",
                report.violation_count,
                written,
            )
        elif report.conforms:
            logger.info("SHACL validation: graph conforms (0 violations).")
        return report


def _shape_label(shape: Optional[URIRef]) -> Optional[str]:
    if shape is None:
        return None
    return str(shape)


__all__ = [
    "CCOP",
    "DEFAULT_SHAPES_PATH",
    "DEFAULT_REPORT_PATH",
    "SHACLValidator",
    "ValidationReport",
    "Violation",
    "lpg_to_rdf",
]
