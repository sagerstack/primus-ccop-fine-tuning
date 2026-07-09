"""
Policy Graph CU Teardown tests (Phase 11, 11-04b / D-38).

Pure-unit tests against a stateful FAKE Neo4j driver -- no live Neo4j, runs
under `pytest -m "not integration"`. The LIVE destructive teardown is
exercised by the 11-04b W4 regen run, not here (a unit test must never delete
the real CU layer).

Covered: snapshot round-trips CU props to JSON; teardown issues the DETACH
DELETE + clears the CU count; the :Clause backbone-preservation guard raises
when the clause count changes; teardown on an empty layer is a safe no-op.
"""

from __future__ import annotations

import json
from typing import Any, Optional

import pytest

from infrastructure.config.settings import get_settings
from rag.graph.ontology.cu_teardown import CUTeardown, TeardownStats


class _FakeResult:
    """Minimal stand-in for a neo4j Result: iterable + `.single()`."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = records

    def __iter__(self):
        return iter(self._records)

    def single(self) -> Optional[dict[str, Any]]:
        return self._records[0] if self._records else None


class _FakeSession:
    """
    Stateful fake session modelling a tiny CU store. Dispatches on query
    substrings; DETACH DELETE flips the CU store to empty so a follow-up
    count reads 0 (models the real before/after).
    """

    def __init__(self, store: "_FakeStore") -> None:
        self.store = store

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def run(self, query: str, **params: Any) -> _FakeResult:
        self.store.queries.append(query)
        if "DETACH DELETE" in query:
            self.store.cus = []
            return _FakeResult([])
        # Dist query also contains "count(cu)" -- must be matched BEFORE the
        # generic CU-count branch.
        if "cu.cu_type AS t" in query:
            dist: dict[str, int] = {}
            for cu in self.store.cus:
                dist[cu["cu_type"]] = dist.get(cu["cu_type"], 0) + 1
            return _FakeResult([{"t": t, "n": n} for t, n in dist.items()])
        if "count(cu)" in query:
            return _FakeResult([{"c": len(self.store.cus)}])
        if "count(c)" in query and "Clause" in query:
            # The backbone-mutation fault injector decrements after delete.
            n = self.store.clause_count
            if self.store.mutate_backbone_on_read and "DETACH" in "".join(self.store.queries):
                n = self.store.clause_count - 1
            return _FakeResult([{"c": n}])
        if query.lstrip().startswith("MATCH (cu:ComplianceUnit)\nOPTIONAL MATCH"):
            return _FakeResult(
                [
                    {"cu": {k: v for k, v in cu.items() if k != "_clause"}, "source_clause_id": cu.get("_clause")}
                    for cu in self.store.cus
                ]
            )
        raise AssertionError(f"Unexpected query: {query!r}")


class _FakeStore:
    def __init__(self, cus: list[dict[str, Any]], clause_count: int = 883) -> None:
        self.cus = list(cus)
        self.clause_count = clause_count
        self.mutate_backbone_on_read = False
        self.queries: list[str] = []


class _FakeDriver:
    def __init__(self, store: _FakeStore) -> None:
        self.store = store

    def session(self, database: Optional[str] = None) -> _FakeSession:
        return _FakeSession(self.store)


def _cu(cu_id: str, cu_type: str = "actor-CU", clause: str = "5.7.1", **extra: Any) -> dict[str, Any]:
    return {"cu_id": cu_id, "source_doc": "CCoP 2.0", "cu_type": cu_type, "_clause": clause, **extra}


class TestSnapshotUnit:
    def test_snapshot_round_trips_cu_props(self, tmp_path):
        store = _FakeStore([_cu("CCoP-5.7.1", subject="CIIO"), _cu("CCoP-5.7.2", cu_type="meta-CU")])
        teardown = CUTeardown(settings=get_settings(), driver=_FakeDriver(store))
        out = tmp_path / "snap.json"

        n = teardown.snapshot(out)

        assert n == 2
        payload = json.loads(out.read_text())
        assert payload["count"] == 2
        first = payload["compliance_units"][0]
        assert first["cu_id"] == "CCoP-5.7.1"
        assert first["subject"] == "CIIO"
        assert first["source_clause_id"] == "5.7.1"

    def test_snapshot_empty_layer_writes_empty_list(self, tmp_path):
        store = _FakeStore([])
        teardown = CUTeardown(settings=get_settings(), driver=_FakeDriver(store))
        out = tmp_path / "snap.json"

        assert teardown.snapshot(out) == 0
        assert json.loads(out.read_text())["compliance_units"] == []


class TestTeardownUnit:
    def test_teardown_deletes_all_cus_and_preserves_backbone(self, tmp_path):
        store = _FakeStore([_cu("CCoP-5.7.1"), _cu("CCoP-1.2.1", cu_type="premise")])
        teardown = CUTeardown(settings=get_settings(), driver=_FakeDriver(store))

        stats = teardown.teardown(snapshot_path=tmp_path / "snap.json")

        assert isinstance(stats, TeardownStats)
        assert stats.cu_count_before == 2
        assert stats.cu_count_after == 0
        assert stats.cus_cleared is True
        assert stats.backbone_preserved is True
        assert stats.clause_count_before == stats.clause_count_after == 883
        assert stats.snapshot_records == 2
        assert any("DETACH DELETE" in q for q in store.queries)

    def test_teardown_records_pre_delete_type_distribution(self, tmp_path):
        store = _FakeStore(
            [_cu("a"), _cu("b"), _cu("c", cu_type="meta-CU"), _cu("d", cu_type="premise")]
        )
        teardown = CUTeardown(settings=get_settings(), driver=_FakeDriver(store))

        stats = teardown.teardown(snapshot_path=tmp_path / "s.json")

        assert stats.type_distribution_before == {"actor-CU": 2, "meta-CU": 1, "premise": 1}

    def test_teardown_on_empty_layer_is_noop(self, tmp_path):
        store = _FakeStore([])
        teardown = CUTeardown(settings=get_settings(), driver=_FakeDriver(store))

        stats = teardown.teardown(snapshot_path=tmp_path / "s.json")

        assert stats.cu_count_before == 0
        assert stats.cu_count_after == 0
        assert stats.backbone_preserved is True

    def test_teardown_raises_if_backbone_count_changes(self, tmp_path):
        store = _FakeStore([_cu("a")])
        store.mutate_backbone_on_read = True  # inject a backbone-count change post-delete
        teardown = CUTeardown(settings=get_settings(), driver=_FakeDriver(store))

        with pytest.raises(RuntimeError, match="altered the :Clause backbone"):
            teardown.teardown(snapshot_path=tmp_path / "s.json")
