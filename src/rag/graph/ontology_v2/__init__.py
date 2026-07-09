"""Corpus-wide CCoP domain ontology + concept graph (v2).

Blind, corpus-wide successor to the hand-pooled OMD POC (B01/B05). Builds a
domain ontology S=(E,R,Φ) over ALL clauses, persists a :Concept layer in Neo4j
tagged by build_id (droppable), with measured coverage + cross-doc linkage.

All counts are re-verified at runtime by query — never hardcoded.
"""
