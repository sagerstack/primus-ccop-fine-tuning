# 11 Motivation: A GraphRAG Ablation Study to Close the Hybrid-RAG Gap

> Term-3 mid-term addendum to the Term-2 Final Report above. The Term-2 body (ground-truth expansion,
> the hybrid RAG pipeline, and the six-dimension LLM-Judge) remains the baseline. Everything from
> Section 11 onward is new Term-3 work, reported at mid-term status: the methodology is built and
> validated on anchor cases, with the full-suite benchmark still in progress.

Term 2 quantified what hybrid (naïve) RAG closes and, just as importantly, what it does not. Two residual
gaps survived retrieval augmentation.

First, **citation correctness (dimension D6) stayed low even with retrieval, at 0.278**. Flat hybrid
retrieval improves the *rate* of correct citation but does not eliminate misattribution: the model still
cites a real clause whose substantive content does not match the claim. The Clause 5.2.1 misattribution in
the Term-2 worked example (Section 9.3) is the canonical case.

Second, **cross-clause and multi-hop compliance answers are invisible to flat chunk retrieval**. A CCoP
answer is frequently distributed across several documents. B01 applicability, for instance, turns on the
CCoP digital-boundary definition, together with the Response-to-Feedback clarification at paragraph 2.2,
together with the Cybersecurity Act designation at section 7. These three passages share almost no
vocabulary, so retrieval by text similarity surfaces one of them and misses the connection between them.

Term 3 attacks these two residuals by deepening the retrieval layer with *structure*: linking clauses
through an explicit, typed knowledge graph rather than an unstructured vector index. The central question
of the term is empirical: **does GraphRAG improve on hybrid (naïve) RAG, and on which dimensions?** To
answer it cleanly, Term 3 is designed as a **controlled ablation study**. The model under evaluation
(Llama-Primus-Reasoning), the independent judge (Qwen3-235B), and the ground-truth suite are all held
fixed, and only the retrieval layer is changed across three settings: no retrieval, hybrid RAG, and
GraphRAG. Because only one variable moves, any measured difference is attributable to the retrieval
*structure* alone. The hypothesis is that a graph in which clauses bridge through shared typed concepts
closes the citation-correctness and cross-clause residual that flat vector retrieval cannot, without
regressing the dimensions hybrid RAG already handles well.

# 12 What Is GraphRAG

Naïve RAG, the Term-2 hybrid pipeline, retrieves a flat set of text chunks by vector and keyword
similarity and hands them to the language model. It carries no notion of how one chunk *relates* to
another, so an answer that requires joining facts across chunks or across documents depends on all the
pieces happening to be lexically similar to the query. For regulation, they frequently are not.

GraphRAG first builds a **knowledge graph** from the corpus: concepts become nodes, and typed
relationships become the edges between them. Retrieval then works by traversing that graph, so the unit of
retrieval is a *connected structure* rather than an isolated chunk. This makes multi-hop and
cross-document reasoning a first-class capability: two clauses in different documents that share a concept
are reachable through that shared node even when their wording is completely different.

The Term-3 design draws its GraphRAG blueprint from the **OMD-GraphRAG** paper (Wang, Huang, Ge, Su, Liu
and Lian, *Enhancing GraphRAG with Ontology-Guided Extraction, Multi-Dimensional Clustering and
Dual-Channel Fusion*, China Unicom, arXiv 2603.25152v3, 2026). That paper extends the widely used
open-source GraphRAG approach and reports a **9.21% average-F1 improvement** over a leading baseline
(LightRAG) on a public multi-hop question-answering benchmark. It contributes three innovations. The first
and third map directly onto compliance reasoning; the second is deferred as low value for our
clause-level factoid ground truth.

1. **Ontology-guided knowledge extraction.** A predefined schema constrains what the extractor may
   produce and discards type-invalid facts. The paper reports this alone improves retrieval accuracy by
   3.17%. This is discussed in Section 13.
2. **Multi-dimensional community clustering.** Richer thematic summaries for broad, global questions
   (3.43%). This is deferred in our build, since our questions are clause-level rather than thematic.
3. **Dual-channel retrieval fusion.** A graph channel and a thematic channel, combined with a traditional
   text-similarity channel and re-ordered by a cross-encoder reranker (3.32%). This is discussed in
   Section 16.

Two further papers frame the design. **GraphCompliance** (Chung and colleagues, *Aligning Policy and
Context Graphs for LLM-Based Regulatory Compliance*, accepted at The Web Conference 2026) supplies an
important cautionary finding: a graph used *only* to retrieve, without deeper structural reasoning, can
actually underperform ordinary RAG (47.5 versus 49.5 micro-F1 in their study). The benefit comes from
structure and reasoning, not from merely attaching a graph to the same ranking. A third paper, *An
Ontology-Driven Graph RAG for Legal Norms* (2025), motivates treating the clause hierarchy as the primary
backbone of the graph. The full research trajectory through these papers is recorded in Section 17.5.

# 13 Ontology-Guided Knowledge Graph, and Why It Beats Typical GraphRAG

Typical GraphRAG extracts facts by **schema-free prompting**: the language model is simply asked to find
the entities and relations in the text, with no constraint on which types are allowed. On regulatory text
this fails in a specific, observed way. An earlier Term-3 baseline built exactly such an un-governed graph
and found that it modelled **the scenario narrative rather than the regulation**. It produced no concept
for a clause, a control, or an obligation; it dumped whole clause sentences in as free-text nodes; and it
generated duplicate and mistyped entities. A graph like that cannot bridge B01 across three documents,
because the phrase "the CII's digital boundary" never resolves to a single, reusable concept.

Ontology-guided extraction fixes this by defining, in advance, a formal schema with three parts:

- A fixed set of permissible **entity types**, such as *CII*, *CIIO*, *Digital Boundary*, *Password*,
  *Security Control*, *Regulator*, and *Obligation*.
- A fixed set of allowable **relationship types**, such as *applies to*, *within boundary*, *determined
  by*, *attribute of*, *mandates*, and *defers to*.
- A **type-constraint rule** for every relationship, specifying which entity types may sit on each side of
  it. A candidate fact is kept only if both endpoints have the correct type; otherwise it is discarded
  after extraction.

Why this works better for compliance, in concrete terms:

- **Every mention of a concept collapses to one canonical node.** "CII", "critical information
  infrastructure", and "the designated system" all become the single *CII* node. That is precisely what
  turns *CII* into a hub that bridges documents. Schema-free extraction instead scatters these into many
  near-duplicate free-text nodes that never connect.
- **The type-constraint rule suppresses the noise that pollutes flat retrieval.** A fact that would
  type-check to nonsense, such as an audit being the thing that "mandates" something, is dropped rather
  than stored, so the graph carries only regulation-shaped structure.
- **Domain law is encoded as explicit rules.** Our ontology asserts, for example, that a system cannot be
  classified as both IT and OT at once; it records thirty "is-a" hierarchy relationships; and it captures
  the distinction between mandatory ("shall") and recommended ("should") obligations. These are exactly
  the distinctions the Term-2 judge measured and that the base model frequently got wrong.

Our one deliberate departure from the paper concerns *who does the extraction*. The paper drives
extraction with a general-purpose language model following the schema prompt. Our trial of a lightweight
model (GPT-4o-mini) under the same schema proved too weak for regulatory text: it dumped free text,
mistyped entities, and varied from run to run. Since the ontology itself was authored to a high standard,
the graph is built to match: **Claude Opus reads each clause and writes the typed facts, and the software
only validates them against the schema and stores them.** Extraction is therefore a one-time cost,
amortised across every future query. The result is a fully governed graph: all 869 clauses extracted,
1,935 typed facts, none violating the schema, resolving to 122 canonical concepts.

# 14 System Architecture with GraphRAG

GraphRAG is added as a **new, self-contained retrieval path**. The Term-2 hybrid pipeline is left
completely untouched and remains the default, honouring the project rule that any new retrieval mode must
be strictly additive and preserve backward compatibility. A user selects the GraphRAG path with a single
mode option; every existing mode behaves exactly as before.

**Indexing (performed once).** A build pipeline turns the seven source documents into the knowledge graph
through the following stages.

| Stage | What it does |
|---|---|
| Re-parsing and cleaning | Re-reads each source PDF from scratch and segments it into 869 clean clauses (nothing is reused from the Term-2 index) |
| Ontology specification | The locked schema: roughly 123 entity types, 64 relationship types, the type-constraint rules, the "is-a" hierarchy, the IT/OT disjointness rule, and obligation modality |
| Governed extraction | Opus-authored facts are validated against the schema and stored, one clause at a time, so the build is resumable |
| Enrichment passes | Additional passes add mandatory-versus-recommended modality (248 clauses) and split broad umbrella concepts into specific leaf concepts |
| Graph loading | The clause nodes, concept nodes, and their relationships are loaded into a graph database under a versioned, removable build tag |
| Retrieval aids | Concept rarity weights, a semantic (dense-vector) index over clause text, and 68 glossary definition nodes are computed to support retrieval |

**A new store.** A local **graph database (Neo4j)** joins the Term-2 vector store. It holds the knowledge
graph and is consulted only by the GraphRAG path.

**A new retrieval step.** A standalone GraphRAG retrieval component reads only the knowledge graph and
touches no existing part of the pipeline. When the GraphRAG mode is selected, the query is routed to this
component, which assembles the grounding context in the same shape used by the hybrid pipeline. The
downstream answer-generation step, in which the model reasons over the retrieved clauses and cites them,
is therefore identical across all modes. This is what keeps the ablation comparison fair.

**Backward compatibility.** The integration is confined to a few well-defined connection points and adds
the GraphRAG mode without modifying any existing mode, retrieval step, or data store. The GraphRAG path is
strictly opt-in.

# 15 Ontology-Guided Knowledge Graph Construction

Construction proceeds clause by clause. Opus reads a clause, writes the typed facts it contains, the
software validates each fact against the schema, and the graph loader records the links between clauses
and the concepts they invoke, as well as the links between concepts. The finished graph contains 863
clause nodes, 122 concept nodes, and 68 glossary-definition nodes, joined by 3,135 clause-to-concept links
and 1,935 concept-to-concept relationships, with no fact violating the schema.

The schema itself is the formal ontology, written as three parts: the entity types (E), the relationship
types (R), and the type-constraint rules (Φ). The three subsections below describe how each part was
defined, what it contains, and how the finished graph is populated against it.

## 15.1 Entity Types (E)

An entity type is a *kind of thing* the regulation talks about, at the level of a type rather than an
individual item. This is a deliberate design choice: a domain controller, a DNS server, and an
operational-technology historian are all treated as the single type *Server*, and the specific make or
model is recorded as a property of the node rather than as a new type. This keeps the vocabulary compact
and reusable, which is what allows different clauses to converge on the same concept.

The entity types were identified by hand, by reading the entire corpus in two passes. The first pass
worked top-down from the structure of the Code of Practice (its chapters on scope, audit, governance,
asset identification, protection, detection, response, resilience, training, and operational technology)
together with the distinctions the eighteen benchmarks require. The second pass worked bottom-up from
every glossary term and from the subject and object of every obligation clause, since these nouns are
exactly the things the graph must be able to link.

This produced **122 entity types, organised into nine categories.** A single abstract parent type,
*Actor*, sits above all duty-bearing roles, and 37 "is-a" relationships record the hierarchy among types
(for example, a Chief Information Security Officer is an Organisational Role, which is an Actor; a Cloud
Service Provider is a Third Party).

| Category | Types | Representative entity types |
|---|---|---|
| Systems, assets and boundaries | 20 | Computer System, CII, CII Asset, IT System, OT System, Enterprise Network, Digital Boundary, Essential Service |
| Processes and activities | 20 | Risk Assessment, Threat Modelling, Penetration Testing, Audit, Incident Management, Monitoring |
| Actors and roles | 18 | CIIO, Board, Chief Information Security Officer, Auditor, Third Party, Incident Response Team |
| Documents, plans and artifacts | 14 | Policy, Risk Register, Incident Response Plan, Audit Report, Remediation Plan |
| Security controls | 13 | Security Control, Access Control Mechanism, Cryptography, Network Control, Security Configuration Baseline |
| Regulatory and legal | 12 | Regulator, Legislation, Code of Practice, Provision, Obligation, Waiver, Designation |
| Risk and threat concepts | 11 | Cybersecurity Risk, Residual Risk, Cybersecurity Threat, Vulnerability, Likelihood, Impact |
| Security objects and data | 8 | Account, Privileged Account, Password, Password Length, Default Credential, Hash Storage |
| Governance and compliance | 6 | Design Principle, Compliance Status, Condition, Compliance Gap, Deadline |
| **Total** | **122** | |

In the finished graph, 107 of these types appear as canonical concept nodes, joined by a further 15 leaf
nodes that specialise a parent type (for example, DNSSEC is recorded as a specific kind of Cryptography,
and a firewall as a specific kind of Network Control), giving 122 concept nodes in all. The most heavily
invoked types are the ones at the centre of the compliance frame: the CIIO appears in 382 clauses, the
generic Provision in 328, and the CII itself in 296.

## 15.2 Relationship Types (R)

A relationship type is a *typed predicate* that connects two entity types, capturing the verbs and duties
the clauses express. Relationships were drawn from the same two-pass reading of the corpus: each obligation
or statement of fact in a clause becomes one or more relationships between the entities it names.

This produced **72 relationship types**, of which **71 are actually used** in the finished graph, across
**1,935 relationships** in total. They fall into a handful of functional families.

| Family | Purpose | Representative relationships |
|---|---|---|
| Applicability and scope | Fix what the regulation covers and where its boundary lies | applies-to, delivers, in-sector, within-boundary, determined-by, designates, connected-to, excluded-from-scope, classified-as |
| Obligation and modality | Distinguish mandatory from recommended duties and their conditions | mandates, recommends, conditioned-on, has-obligation, has-deadline |
| Control and protection | Link controls to what they protect or mitigate | implements, protects, mitigates, detects, applies-principle |
| Threat and risk | Connect threats, vulnerabilities and the activities that address them | identifies, targets, addresses, responds-to |
| Accountability and governance | Assign duties and reporting lines across roles | delegates-to, responsible-for, reports, conducts, has-certification |
| Incident and response | Capture the response lifecycle | activates, recovers, remediated-by |
| Limitation and deferral | Record what the regulation does *not* specify | does-not-specify, defers-to, excluded-from-scope |

The most frequent relationships reflect the regulation's emphasis on controls and duties: *implements*
appears 248 times, *mandates* 200, *protects* 196, *mitigates* 85, and *identifies* 82. The
limitation-and-deferral family is small but important, because it is what lets the graph represent the
absence of a requirement (for example, that the Code does not specify a password length), which is central
to the hallucination-resistance benchmarks.

## 15.3 Type-Constraint Rules (Φ)

Φ is what makes the extraction *governed* rather than free-form. It assigns to every one of the 72
relationships a permitted **domain** (the entity types allowed on the subject side) and a permitted
**range** (the entity types allowed on the object side). A candidate fact is admitted into the graph only
if the subject's type is in the relationship's domain and the object's type is in its range; any fact that
fails this check is discarded after extraction. A few example rules:

| Relationship | Permitted subject types (domain) | Permitted object types (range) |
|---|---|---|
| applies-to | Provision, Code of Practice | CII, CIIO, IT System, OT System |
| delivers | CII, Computer System | Essential Service |
| within-boundary | CII, CII Asset, Computer System | Digital Boundary |
| determined-by | Digital Boundary | Regulator |
| classified-as | CII | IT System, OT System |

The constraints are not one-to-one: 34 of the relationships permit more than one subject type and 38
permit more than one object type, which is what lets a single relationship like *applies-to* connect the
regulation to several kinds of governed system while still rejecting nonsensical pairings. Φ is
complemented by one hard **disjointness rule**: a system cannot be classified as both IT and OT at the
same time, which is the distinction the IT/OT boundary benchmark depends on.

Because every fact passes through Φ at construction time, the finished graph is fully type-consistent:
all 869 clauses were processed and none of the 1,935 stored relationships violates the schema. This is the
concrete difference from schema-free GraphRAG, where no such check exists and the noise it admits is what
pollutes retrieval.

## 15.4 Clauses as Nodes, Linked to the Concept Graph

The concept layer so far is only half of the graph. The other half is the regulation itself: **every
clause is also stored as its own node**, linked to the concepts it invokes. This join connects the
regulatory text to the concept structure and is what lets the system retrieve the *right clauses* for a
question. There are **863 clause nodes**, one per clause, spanning the seven source documents:

| Source document | Clause nodes |
|---|---|
| CCoP 2.0 | 379 |
| CCoP Response to Feedback | 280 |
| Security By Design | 98 |
| Cybersecurity Act 2018 | 62 |
| Auditing Guidelines | 17 |
| Risk Assessment Guide | 15 |
| Threat Modelling Guide | 12 |
| **Total** | **863** |

Each clause node carries its citation identifier (for example, "CCoP 2.0, clause 5.9.2(b)"), its source
document, and its **verbatim text**, since it is this exact text that grounds and is cited by the model,
so the graph never paraphrases the regulation. Each node is then linked to the concepts appearing in it by
an **invokes** relationship, giving **3,135 links**: 840 of the 863 clauses invoke at least one concept
(3.73 on average), and the remaining 23 are administrative or header clauses left unlinked rather than
padded with noise. A glossary layer completes the picture, with 68 definition nodes attaching
authoritative text to the concepts they define through 28 links.

The result is a **two-layer graph**: a text layer of clause nodes holding verbatim regulation, and a
meaning layer of concepts joined by the typed relationships of Section 15.2, stitched together by the
invokes links. This is what enables clause retrieval: a question is mapped to the concepts it concerns,
and the graph returns the clauses that invoke them. Because concepts are shared, a single concept becomes
a hub that gathers clauses across documents. The CII concept, for instance, is invoked by 296 clauses
spanning all seven documents, so a scope question anchored on the CII reaches the CCoP definition, the
Act's designation, and the Response-to-Feedback clarification together, even though their wording differs.
Section 16 describes the retrieval procedure that walks this structure.

## 15.5 Composing Typed Facts into Cross-Document Bridges

The graph's value appears when typed facts combine: a concept that several clauses invoke becomes a bridge
across documents. The two anchor benchmarks illustrate this, using the actual extracted facts.

**B01-001, applicability and scope.**

> *A healthcare provider's patient monitoring systems and MRI machines have been designated as CII. Their
> hospital administration system (patient records, billing, appointments) shares the same enterprise
> network. Does CCoP 2.0 mandatory compliance extend to the hospital administration system?*

The expected answer is *not applicable*: compliance follows the CII's digital boundary as determined by
the regulator, not another system merely sharing the same enterprise network. That answer is distributed
across three documents, which the graph links through the shared concepts *CII* and *Regulator*.

| Source clause (document) | Facts extracted into the graph |
|---|---|
| CCoP 2.0, clause 1.4.1 | the Code of Practice *applies to* the CII; the Code of Practice *applies to* the CIIO |
| Response-to-Feedback, paragraph 2.2 | the Code of Practice *applies to* the CII; the CII is *within* the Digital Boundary; the Digital Boundary is *determined by* the Regulator |
| Cybersecurity Act, section 7 | the Regulator *designates* a Computer System; that Computer System *delivers* an Essential Service |

Though the three clauses share almost no wording, they form one connected structure: clause 1.4.1 and
paragraph 2.2 both point to *CII*, while paragraph 2.2 and section 7 both point to *Regulator*. The
decisive scope fact, that the boundary is the CII's digital boundary as determined by the regulator and
not the enterprise-network perimeter, is exactly the path *CII → within → Digital Boundary → determined by
→ Regulator*, which a flat index cannot represent.

**B05-001, control comprehension (password requirements).**

> *What are the minimum password requirements according to CCoP 2.0?*

The expected answer is that CCoP 2.0 specifies *no* password length or complexity requirement and defers
to industry standards such as NIST; its only password obligations are that default passwords be changed
and passwords stored in hashed form. This is a common hallucination trap, since a model is tempted to
invent a minimum length. The answer bridges two documents through the shared concept *Password*.

| Source clause (document) | Facts extracted into the graph |
|---|---|
| CCoP 2.0, clause 5.9.2(b) | a Password is *stored as* a hash; the Security Configuration Baseline requires default credentials to be *changed* |
| Response-to-Feedback, paragraph 11.28 | Password Length is an *attribute of* Password; the Code of Practice *does not specify* a Password Length; the CIIO *defers to* an external standard |

The control clause and the clarification are joined by the shared *Password* concept, so the fact that the
Code defers on password length, the correct answer and the trap, is reachable from the control clause
through that bridge.

# 16 GraphRAG Retrieval Methodology

Retrieval turns a question into a small set of the most relevant clauses, handed to the model as
grounding, in four stages: translate the question into graph concepts (16.1), expand those concepts across
the graph (16.2), recall candidate clauses through three parallel channels (16.3), and fuse and re-rank
them into the final list (16.4). Known limitations follow in 16.5.

## 16.1 Stage 1: From the User Query to Graph Concepts

This first stage is what makes the method GraphRAG rather than ordinary search. The question is not
embedded and matched against clause text directly; it is first **translated into the graph's concept
vocabulary**, the same canonical concepts the clauses invoke (Section 15), so that question and clauses
meet in one shared conceptual space and a relevant clause can be found even when it shares no words with
the question.

The translation is done by a **language model acting as a constrained classifier**: a lightweight model
(GPT-4o-mini, at temperature zero) is shown the full list of the graph's 122 concept names and returns
only those, chosen word-for-word from the list, that the question is *about*. Because it may pick only
from a fixed vocabulary, this is bounded selection rather than open-ended generation, so a small model is
reliable here, unlike the graph *construction* step which required Claude Opus (Section 13). It selects by
meaning rather than keyword (for example, "patient monitoring systems" and "MRI machines" are read as a
*Computer System* and a *CII Asset*, not the *Monitoring* control), it surfaces implicit concepts the
question depends on but never names (scope questions always surface *Digital Boundary*, *Obligation*, and,
when contested, *Regulator*), and it prefers specific concepts over broad hubs, returning a focused two to
six. For the anchor questions of Section 15.5 it yields *Digital Boundary*, *CII*, *Obligation*, and
*Regulator* for B01-001, and *Password* and *Password Length* for B05-001.

## 16.2 Stage 2: Expanding Across the Graph

The selected concepts are extended by one step along the concept relationships, so clauses invoking a
closely related concept are also considered. The expansion is **gated by concept rarity**: only specific,
informative concepts expand, while a broad hub such as *CII* (which touches roughly a third of the graph)
counts as a direct match but does not pull in neighbours, preventing it from flooding the candidate set.

## 16.3 Stage 3: Three Parallel Recall Channels

The question and its concepts are run through three complementary channels, each returning its own ranked
list of candidate clauses, adapting the reference paper's dual-channel design so that a clause missed by
one channel can still be found by another.

- **Graph channel (structural):** scores each clause by how many query concepts it invokes, weighted by
  concept rarity, so a rare decisive concept outweighs a common one and a focused answer outranks a
  generic clause that merely shares common concepts.
- **Keyword channel:** a classical keyword search over verbatim clause text, strongest on exact
  terminology and clause numbers.
- **Semantic channel:** a dense-vector similarity search over clause text, catching abstract clauses that
  concept overlap and keyword match both miss.

## 16.4 Stage 4: Fusion, Re-ranking, and Grounding

The three lists are merged by a **weighted rank fusion** (combining by position, weighting the semantic
channel highest, the graph channel next, the keyword channel least). A **cross-encoder reranker** then
scores each question-and-clause pair in the merged pool; its ordering is combined with the fused ranking
rather than used alone, because the current reranker gives undifferentiated scores on very short
questions. A final **glossary step** attaches authoritative definitions of the query concepts as extra
grounding, independent of the ranking. The top clauses, in verbatim text with their definitions, form the
grounding context, assembled in the same shape the hybrid pipeline uses so that answer generation is
identical across modes.

## 16.5 Known Limitations

Two ranking issues remain before the mode is finalised: the rank fusion can dilute a result that is strong
in a single channel but weak in the others, and the cross-encoder gives weak, clustered scores on very
short factoid questions. Both point to the reranker as the next lever to improve, whether by adapting its
influence to its own confidence or by adopting the stronger reranker used in the reference paper.

# 17 Evaluation

## 17.1 First End-to-End Result: B05-001, Hybrid versus GraphRAG

The GraphRAG mode has now been run end-to-end through the evaluation harness, and the first head-to-head
result on the B05-001 anchor case gives a concrete, single-case illustration of the thesis of Section 11.
Both modes used the same model, the same judge, and the same six-dimension rubric; only the retrieval
layer differed.

The ground truth for this case is as follows.

- **Question:** *What are the minimum password requirements according to CCoP 2.0?*
- **Expected answer:** CCoP 2.0 specifies no password length or complexity requirement. Per
  Response-to-Feedback paragraph 11.28, CSA defers to industry standards such as NIST for the appropriate
  password length. The only password obligations, in CCoP 2.0 clause 5.9.2(b), are that default passwords
  be changed and that passwords be stored in hashed form.
- **Expected clause citations:** Response-to-Feedback paragraph 11.28, and CCoP 2.0 clause 5.9.2(b).

The two modes behaved as follows.

| Aspect | Hybrid (naïve RAG) | GraphRAG |
|---|---|---|
| Clauses retrieved | 3 | 8 |
| Expected clauses retrieved | 0 of 2 (returned clauses 5.1.2, 5.6.1 and Response-to-Feedback section 6, none of which govern passwords) | 2 of 2 (both paragraph 11.28 and clause 5.9.2(b) retrieved, alongside the 5.9.2 parent) |
| Raw model response (verbatim) | Minimum Password Requirements in CCoP 2.0<br/><br/>CCoP 2.0 does not explicitly outline specific minimum password requirements such as length, complexity, or frequency of changes. The code focuses on broader authorization and authentication controls (Clause 5.1.2) and network access control rules (Clause 5.6.1), but it does not specify detailed technical specifications for passwords.<br/><br/>The emphasis is on implementing measures commensurate with the cybersecurity risk profile rather than prescribing exact password policies. Therefore, CIIOs are expected to assess their specific risks and implement authentication controls that align with these assessments, without explicit minimum requirements provided by CCoP 2.0.<br/><br/>Sources: CCoP 2.0 Clause 5.1.2; CCoP Response to Feedback Section 6 | Minimum password requirements according to CCoP 2.0 are not explicitly stated.<br/><br/>The regulatory corpus does not specify a minimum password length or complexity for passwords or passphrases under the Cybersecurity Code of Practice (CCoP) 2.0. While it emphasizes the importance of managing passwords and passphrases, including changing default passwords and storing them in hashed forms, it does not provide specific requirements regarding their length.<br/><br/>Sources: CCoP Response to Feedback 11.28; CCoP 2.0 5.9.2(b) |
| Citations the model gave | Clause 5.1.2 and Response-to-Feedback section 6, neither of which is a governing clause | Paragraph 11.28 and clause 5.9.2(b), both of them the expected clauses |
| Were citations used correctly? | No | Yes |

The LLM-Judge scores (each dimension out of 3) sit side by side as follows.

| Dimension (out of 3) | Hybrid | GraphRAG |
|---|---|---|
| D1 verdict accuracy | 1 | 3 |
| D2 justification quality | 2 | 3 |
| D3 factual grounding | 1 | 2 |
| D4 scope appropriateness | 3 | 3 |
| D5 actionable way forward | 0 | 1 |
| D6 citation correctness | 0 | 2 |
| **Composite (0 to 1)** | **0.39** | **0.78** |

Both models reached the same surface verdict, that no minimum is specified, but only GraphRAG grounded
that verdict in the two clauses that actually govern it. Hybrid retrieved none of the governing clauses
(its three chunks concerned access control and network access, not passwords), so its answer omitted the
deferral to NIST and the change-default and hashed-storage obligations, and it cited clauses that do not
contain the answer. This is exactly the Term-2 failure mode: a plausible answer resting on wrong
citations, which is what the citation-correctness dimension (D6) is designed to catch, and which cost
hybrid a zero there. GraphRAG's concept bridge on *Password* surfaced both paragraph 11.28 and clause
5.9.2(b), lifting citation correctness from 0 to 2 and verdict accuracy from 1 to 3, and the composite
from 0.39 to 0.78. This is a single case, on the benchmark the graph was designed around, and the
reranker's scores were tightly clustered (a known limitation, Section 16.5); it illustrates the mechanism
rather than establishing a suite-level claim. The full ablation of Section 17.4 remains the real test.

## 17.2 Second End-to-End Result: B01-001, Hybrid versus GraphRAG

The second head-to-head, on the B01-001 scope case, is a sharper illustration still, because here the two
modes disagree on the answer itself. The setup is again identical across modes except for retrieval.

The ground truth for this case is as follows.

- **Question:** *A healthcare provider's patient monitoring systems and MRI machines have been designated
  as CII. Their hospital administration system (patient records, billing, appointments) shares the same
  enterprise network. Does CCoP 2.0 mandatory compliance extend to the hospital administration system?*
- **Expected answer (label: not applicable):** compliance applies to the designated CII and its digital
  boundary, not automatically to every system on the same enterprise network, so the hospital
  administration system is not in scope merely for sharing the network. The digital boundary is jointly
  determined by CSA, the CIIO, and the Sector Lead, and is not the enterprise-network perimeter.
- **Expected clause citations:** CCoP 2.0 clauses 1.2.1 and 1.4.1, and Cybersecurity Act section 7, with
  Response-to-Feedback paragraph 2.2 as the decisive digital-boundary clause.

The two modes behaved as follows.

| Aspect | Hybrid (naïve RAG) | GraphRAG |
|---|---|---|
| Clauses retrieved | 3 | 9 |
| Expected clauses retrieved | None (returned clauses 3.3.1, 5.12.1 and 5.6.1, on governance and network controls, none about scope) | The decisive digital-boundary clause, Response-to-Feedback paragraph 2.2, plus the surrounding scope cluster (paragraphs 2.1, 2.5, 2.11) |
| Verdict reached | **Wrong**: compliance *does* extend to the administration system | **Correct**: compliance does *not* extend to it |
| Raw model response (verbatim) | Compliance with CCoP 2.0 extends to all systems that are part of the Critical Information Infrastructure (CII).<br/><br/>CCoP 2.0 mandates that CIIOs protect and manage cybersecurity risks across their entire designated CII, which includes both patient monitoring systems and MRI machines as well as the hospital administration system. The regulatory framework emphasizes comprehensive coverage of all components integral to the CII's operation.<br/><br/>Key Points: Definition of CII, CCoP 2.0 defines CII broadly to encompass any information infrastructure essential for national security, public safety, or economic well-being; Scope Inclusion, the administration system, being part of the same enterprise network as the designated systems, falls under the regulatory purview due to its interconnectedness and potential impact on critical services; Comprehensive Protection, CIIOs must safeguard all aspects of their CII, including systems not explicitly listed if they contribute to its functioning or security posture.<br/><br/>Conclusion: given the interconnected nature of modern healthcare IT environments and the potential cascading effects on critical services, compliance with CCoP 2.0 is expected to cover all systems integral to the CII.<br/><br/>Sources: CCoP 2.0 3.3.1(a), 5.6.1, 5.12.1; Cybersecurity Act 2018 Section 11(7) | CCoP 2.0 does not explicitly mandate compliance to the hospital administration system if it is part of the enterprise network separate from the designated CII systems (the patient monitoring and MRI machines).<br/><br/>The regulatory corpus indicates that CCoP 2.0 applies specifically to the CII systems, defined as an infocomm or operational technology system or network infrastructure vital to the continuous delivery of Essential Services (Security By Design Annex C). The CII includes computer systems within its digital boundary as defined by CSA, CIIOs, and Sector Leads (Response-to-Feedback 2.2).<br/><br/>While the hospital administration system shares the same enterprise network with the MRI machines and patient monitoring systems, there is no explicit requirement in CCoP 2.0 that extends compliance beyond the designated CII boundaries. Clauses such as 10.2.1 emphasize physical segregation between OT CII networks and enterprise networks, suggesting a focus on isolating critical infrastructure from other systems.<br/><br/>Therefore, based on the regulatory corpus, compliance with CCoP 2.0 is limited to the designated CII systems as defined by CSA and CIIOs, not extending to other parts of the enterprise network unless explicitly included in the CII designation.<br/><br/>Sources: Security By Design Annex C; Response-to-Feedback 2.2; clause 10.2.1; Response-to-Feedback 11.25 |
| Citations the model gave | Clauses 3.3.1(a), 5.6.1, 5.12.1, and Cybersecurity Act section 11(7), none of which govern scope; section 11(7) is the waiver clause and was neither retrieved nor relevant | The CII definition (Security By Design Annex C), the digital-boundary clause (paragraph 2.2), the segregation clause (10.2.1) and the designation-scope clause (11.25); the governing ideas are cited, though clause 10.2.1 is mislabelled to the wrong document |
| Were citations used correctly? | No | Largely (one document mislabel) |

The LLM-Judge scores (each dimension out of 3) sit side by side as follows.

| Dimension (out of 3) | Hybrid | GraphRAG |
|---|---|---|
| D1 verdict accuracy | 0 | 2 |
| D2 justification quality | 0 | 2 |
| D3 factual grounding | 0 | 2 |
| D4 scope appropriateness | 2 | 3 |
| D5 actionable way forward | 0 | 0 |
| D6 citation correctness | 0 | 1 |
| **Composite (0 to 1)** | **0.11 (fail)** | **0.56 (pass)** |

Where B05 showed a right answer resting on wrong citations, B01 shows the more dangerous failure: a
*confidently wrong verdict*. Hybrid retrieved only governance and network-control clauses, none about
scope, so with nothing to anchor the boundary question it fell back on a plausible but incorrect
"interconnectedness" argument, concluded that compliance extends to the whole network, and even invoked a
Cybersecurity Act section 11(7) waiver citation that is neither relevant nor present in its context. That
answer scored zero on verdict, justification, grounding, and citation, and failed the case at 0.11.
GraphRAG's concept mapping instead surfaced the digital-boundary scope cluster, with the decisive
Response-to-Feedback paragraph 2.2, so the model reasoned correctly that compliance follows the CII's
digital boundary rather than the shared network and reached the correct "not applicable" verdict, passing
at 0.56. As with B05, this is a single case on a benchmark the graph was designed around, GraphRAG's own
citations were imperfect (one clause mislabelled to the wrong document, hence citation correctness of only
1 of 3), and neither mode offered an actionable way forward; the full ablation of Section 17.4 remains the
real test.

## 17.3 Status (Mid-Term, Reported Honestly)

The GraphRAG methodology is built, is now wired into the evaluation harness, and is validated end-to-end
on the two anchor benchmarks, B01 and B05, chosen because each exercises a distinct graph capability: B01
a three-document scope bridge, B05 a two-document control-and-clarification bridge. The worked bridges
(Section 15.5) and the first two results (Sections 17.1 and 17.2) confirm that the graph recalls the
distributed answer that flat retrieval misses.

It is **not yet a full-suite result.** No GraphRAG variant, neither this one nor its three predecessors
(Section 17.5), has yet completed a fair benchmark across the whole ground truth, not even the
eighteen-case stratified sample; only individual anchor cases have been run. The cross-encoder re-ranking
currently takes roughly sixty to ninety seconds per query on the available hardware, so it must be made
faster or run on a graphics processor before the full 435-case study.

## 17.4 The Planned Ablation

The evaluation is the controlled ablation study framed in Section 11: no retrieval, versus hybrid (naïve)
RAG, versus GraphRAG, on the same model, the same judge, and the same ground truth, scored with the same
six-dimension rubric. The primary hypotheses are that GraphRAG lifts **citation correctness** and the
**cross-clause and multi-hop cases**, the two residuals that hybrid RAG left open, above the naïve-RAG
baseline, without regressing the dimensions hybrid RAG already handles well (reasoning quality and scope
appropriateness). The headline read-out will be the per-dimension and per-benchmark improvement of
GraphRAG over hybrid RAG, presented in the same form as the Term-2 Native-versus-RAG comparison
(Section 9) so that the two studies are directly comparable.

## 17.5 Research Arc (Four Iterations)

The current GraphRAG build is the fourth iteration of the Term-3 retrieval work. Each earlier attempt was
a genuine experiment that produced a decisive negative finding, and it is those findings, rather than a
pre-committed plan, that shaped the current design. This is the project's research-first method in action.

| Iteration | Approach | Decisive finding, and why it moved on |
|---|---|---|
| 1. Basic GraphRAG baseline | An un-governed graph built by free (schema-free) extraction with a lightweight model, retrieved through a graph database into the same model. | The extraction modelled the scenario, not the regulation (no clause-level concepts). On the single case tested it scored well below hybrid RAG, but the comparison was confounded because the baseline used very coarse chunks and no re-ranking. This motivated a governed, ontology-grounded graph. |
| 2. Ontology-grounded graph | A curated CCoP ontology was locked and used to govern extraction, with clause nodes seeded and validated. | The ontology governed *extraction* but was never actually *queried* at retrieval time; retrieval remained ordinary chunk search with a thin graph decoration. A literature review then showed that retrieval-only graph use is not enough. |
| 3. Alignment to GraphCompliance | A reasoning-first redesign modelling each obligation as a structured unit, with a per-query context graph and a decision gate. Around 800 obligation units were built. | This design never beat hybrid RAG on the anchor case, and diagnosis showed the failure was a *ranking* problem, not the architecture: the decisive clause was present in the candidate pool but out-ranked by generic material. The obligation-unit model was the wrong investment for a ranking problem. |
| 4. OMD-GraphRAG (current) | A shift from obligation reasoning to an ontology-guided concept graph with multi-channel retrieval (this section). Clauses link to the concepts they invoke, and concepts link to one another, so clauses bridge through shared concept hubs. | Cross-document bridging, the residual from Section 11, becomes native (the B05 password bridge; the B01 CII hub spanning all seven documents). The earlier obligation-unit graph was archived and removed. This is the current work. |

OMD-GraphRAG and GraphCompliance are two different answers to the same diagnosis. GraphCompliance
structures the regulation as obligations and reasons over them; OMD-GraphRAG structures it as an
ontology-guided concept graph and fuses several retrieval channels. Term 3 tried the reasoning-first
answer first, found that it stalled on ranking, and pivoted to the retrieval-fusion answer, carrying
forward the earlier lessons (anchoring to the scenario, and carrying verbatim clause text) while dropping
the obligation-unit model.

## 17.6 Next Steps

1. Resolve the two remaining ranking issues in the retriever, and make the cross-encoder step fast enough
   for a full-suite run (a bounded pool or a graphics processor).
2. Broaden the end-to-end checks beyond the two anchor cases to a wider slice, confirming that the
   ground-truth clauses appear in the top results across benchmarks before making any suite-level claim.
3. Run the ablation: GraphRAG versus hybrid versus no-retrieval on the full 435-case ground truth under
   the six-dimension judge, isolating the citation-correctness and cross-clause-bridging improvements.
4. Report the verdict: whether GraphRAG's structural retrieval measurably improves on hybrid RAG, per
   dimension and per benchmark, and characterise whatever residual the graph still leaves open.
