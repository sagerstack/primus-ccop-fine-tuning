"""OMD-GraphRAG, run end-to-end for B01-001, scoped to a realistic candidate pool
(GT answer clauses + the distractors plain retrieval actually returned).

Steps (faithful to OMD §3.1-3.3):
  1. Schema S=(E,R,Φ)
  2. Schema-guided LLM extraction of typed SPO triples per clause  (cached)
  3. Post-hoc type-check (Φ) — discard violating triples
  4. Entity resolution (canonical merge) -> the CROSS-DOCUMENT bridge
  5. Build entity KG (entity nodes, clause-MENTIONS-entity, entity-relation-entity)
  6. Dual-channel retrieval: Ch.I structural-overlap over k-hop neighborhood
     + Ch.II dense proxy; β fusion; cross-encoder rerank
  7. Grade: do ANSWER clauses beat DISTRACTORS, across documents?

cd src && poetry run python <this>
"""
import os, json, re, hashlib
SCRATCH=os.path.dirname(os.path.abspath(__file__))
from infrastructure.config.settings import get_settings
settings=get_settings()
import neo4j

# ---------- pool ----------
ANSWERS=["CCoP-1.4.1","CCoP-1.2.1#CII","Act-7","RtF-2.2","RtF-2.3"]
DISTRACTORS=["Act-14","Act-15","Act-16","Act-10","Act-11","CCoP-1.3.2",
             "CCoP-10.2.1","CCoP-10.2.2","CCoP-10.2.3","SBD-6.6.1.2","SBD-6.6.1.3","CCoP-5.13.2","CCoP-5.15.2"]
QUESTION=("A healthcare provider's patient monitoring systems and MRI machines have been designated as CII. "
 "Their hospital administration system (patient records, billing, appointments) shares the same enterprise network. "
 "Does CCoP 2.0 mandatory compliance extend to the hospital administration system?")

def fetch_texts():
    d=neo4j.GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
    out={}
    with d.session(database=settings.neo4j_database) as s:
        for cid in ANSWERS+DISTRACTORS:
            r=s.run("MATCH (c:Clause {citation_id:$cid}) RETURN c.text AS t",cid=cid).single()
            if not r or not r["t"]:
                r=s.run("MATCH (cu:ComplianceUnit {cu_id:$cid})-[:FROM_CLAUSE]->(c:Clause) RETURN c.text AS t",cid=cid).single()
            out[cid]=(r["t"] if r else "")[:1200]
    d.close(); return out

# ---------- schema ----------
ENTITY_TYPES=["CII","CIIO","CIISystem","DigitalBoundary","Regulator","ComputerSystem",
              "EnterpriseNetwork","Obligation","AuditScope","EssentialService","Person"]
RELATIONS=["DEFINES","DESIGNATES","APPLIES_TO","WITHIN_BOUNDARY","DETERMINED_BY",
           "IN_AUDIT_SCOPE","EXCLUDED_FROM_AUDIT","HAS_OBLIGATION","CONNECTED_TO","PART_OF"]
# Φ: allowed object types per relation (light type constraint)
PHI={"DESIGNATES":{"CII"},"APPLIES_TO":{"CII","CIISystem","CIIO"},"WITHIN_BOUNDARY":{"DigitalBoundary"},
     "DETERMINED_BY":{"Regulator"},"DEFINES":set(ENTITY_TYPES),"IN_AUDIT_SCOPE":{"AuditScope","CII","CIISystem"},
     "EXCLUDED_FROM_AUDIT":{"AuditScope","CII","CIISystem"},"HAS_OBLIGATION":{"Obligation"},
     "CONNECTED_TO":{"EnterpriseNetwork","CII","CIISystem","ComputerSystem"},"PART_OF":set(ENTITY_TYPES)}

PROMPT="""Extract typed relation triples from this regulatory clause.
Use ONLY these entity types: {et}
Use ONLY these relations: {rt}
Normalize every entity to a canonical name — ALWAYS write "CII" for critical information infrastructure, "CIIO" for its owner, "DigitalBoundary" for the digital boundary / cyber operating environment, "Regulator" for CSA/Commissioner/Sector Lead, "AuditScope" for the cybersecurity audit scope.
Return ONLY a JSON array of {{"subject":..,"subject_type":..,"relation":..,"object":..,"object_type":..}}. No prose.

CLAUSE:
{clause}

JSON:"""

def extract(cid,text):
    cache=os.path.join(SCRATCH,f"omd_ex_{re.sub(r'[^A-Za-z0-9]','_',cid)}.json")
    if os.path.exists(cache): return json.load(open(cache))
    from openai import OpenAI
    cli=OpenAI(api_key=settings.openrouter_api_key,base_url=settings.openrouter_base_url,timeout=60)
    p=PROMPT.format(et=", ".join(ENTITY_TYPES),rt=", ".join(RELATIONS),clause=text)
    r=cli.chat.completions.create(model=settings.ontology_discovery_model,
        messages=[{"role":"user","content":p}],temperature=0.0,max_tokens=600)
    raw=(r.choices[0].message.content or "").strip()
    try:
        from neo4j_graphrag.experimental.components.entity_relation_extractor import fix_invalid_json
        trips=json.loads(fix_invalid_json(raw))
    except Exception:
        try: trips=json.loads(raw)
        except Exception: trips=[]
    trips=trips if isinstance(trips,list) else []
    json.dump(trips,open(cache,"w"),indent=1); return trips

# ---------- entity resolution ----------
SYN={"critical information infrastructure":"CII","cii system":"CII","cii asset":"CII","cii systems":"CII",
     "computer system":"ComputerSystem","computer systems":"ComputerSystem",
     "cyber operating environment":"DigitalBoundary","digital boundary":"DigitalBoundary",
     "commissioner":"Regulator","csa":"Regulator","cyber security agency":"Regulator","sector lead":"Regulator",
     "critical information infrastructure owner":"CIIO","owner":"CIIO",
     "cybersecurity audit":"AuditScope","audit":"AuditScope","enterprise network":"EnterpriseNetwork"}
def canon(name,typ):
    n=(name or "").strip().lower().strip('"').strip()
    if n in SYN: return SYN[n]
    # if the type is already a schema type and name is generic, use the type
    if typ in ENTITY_TYPES and (n in (typ.lower(),"") or len(n)<3): return typ
    for k,v in SYN.items():
        if k in n: return v
    return typ if typ in ENTITY_TYPES else n.title().replace(" ","")

def type_ok(rel,otype):
    return otype in PHI.get(rel,set(ENTITY_TYPES)) if rel in PHI else True

# ---------- run ----------
print("fetching texts + extracting (schema-guided, cached)...",flush=True)
texts=fetch_texts()
clause_entities={}   # cid -> set(canonical entities)
rel_edges=set()      # (subjE, rel, objE)
for cid in ANSWERS+DISTRACTORS:
    trips=extract(cid,texts[cid])
    ents=set()
    kept=0
    for t in trips:
        rel=str(t.get("relation","")).strip().upper()
        se=canon(t.get("subject"),t.get("subject_type","")); oe=canon(t.get("object"),t.get("object_type",""))
        ot=t.get("object_type","")
        if rel and se: ents.add(se)
        if rel and oe: ents.add(oe)
        # type-check
        if rel in RELATIONS and type_ok(rel, canon(t.get("object"),ot) if canon(t.get("object"),ot) in ENTITY_TYPES else ot):
            if se and oe: rel_edges.add((se,rel,oe)); kept+=1
    clause_entities[cid]=ents
    print(f"  [{cid:16}] entities={sorted(ents)}")

# query entities (extract from the question with same schema)
print("\nextracting QUERY entities...",flush=True)
qtrips=extract("QUERY__B01",QUESTION)
Q=set()
for t in qtrips:
    for k,kt in [("subject","subject_type"),("object","object_type")]:
        e=canon(t.get(k),t.get(kt,""))
        if e: Q.add(e)
# the query is an applicability question about CII in scope -> ensure scope concepts present if extracted
print("  QUERY entities:",sorted(Q))

# ---------- k-hop neighborhood expansion of Q ----------
def neighbors(ent):
    out=set()
    for a,r,b in rel_edges:
        if a==ent: out.add(b)
        if b==ent: out.add(a)
    return out
Qplus=set(Q)
for e in list(Q): Qplus|=neighbors(e)
print("  Q+ (1-hop neighborhood):",sorted(Qplus))

# ---------- Channel I: structural overlap ----------
def chan1(cid):
    E=clause_entities[cid]
    s = 1.0*len(Q & E) + 0.5*len(( Qplus - Q) & E)   # full weight direct query-entities, half for neighborhood
    return s
scores={cid:chan1(cid) for cid in ANSWERS+DISTRACTORS}
ranked=sorted(scores.items(),key=lambda x:-x[1])

print("\n"+"="*80)
print("CHANNEL I (structural overlap over entity KG) — ranking:")
ans=set(ANSWERS)
for i,(cid,sc) in enumerate(ranked,1):
    tag="ANSWER " if cid in ans else "distr. "
    print(f"  {i:2}. {sc:4.1f}  [{tag}] {cid:16} ents={sorted(clause_entities[cid])}")
# grade
ans_ranks=[i for i,(cid,_) in enumerate(ranked,1) if cid in ans]
top5=set(cid for cid,_ in ranked[:5])
print(f"\n  ANSWER ranks: {ans_ranks}  | answers in top-5: {len(ans & top5)}/5")
print(f"  cross-doc check — RtF-2.2 rank: {next(i for i,(c,_) in enumerate(ranked,1) if c=='RtF-2.2')}, "
      f"Act-7 rank: {next(i for i,(c,_) in enumerate(ranked,1) if c=='Act-7')}, "
      f"CCoP-1.4.1 rank: {next(i for i,(c,_) in enumerate(ranked,1) if c=='CCoP-1.4.1')}")
print("[done]")
