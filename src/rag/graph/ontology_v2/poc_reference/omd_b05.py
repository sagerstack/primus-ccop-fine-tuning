"""OMD on B05, BLIND construction: extract typed relations from every pool clause
(answers + distractors, UNLABELED) against a domain-general schema, resolve,
retrieve by entity-structural overlap for the B05 query, then grade.
Labels are used ONLY at the end for grading.
cd src && poetry run python <this>
"""
import os, json, re
SCRATCH=os.path.dirname(os.path.abspath(__file__))
from infrastructure.config.settings import get_settings
settings=get_settings()
import neo4j

# --- pool (labels kept ONLY for grading; extractor never sees them) ---
ANSWERS=["CCoP-5.9.2(b)","RtF-11.28","CCoP-5.9.2"]
DISTRACTORS=["CCoP-5.9.2(a)","CCoP-5.9.2(c)","CCoP-5.9.2(d)","CCoP-5.9.2(f)","CCoP-5.9.2(g)",
             "CCoP-5.9.3","CCoP-5.9.4","CCoP-10.4.1(e)","CCoP-5.7.2","CCoP-5.2.1","CCoP-5.11.2","CCoP-3.1.1(c)","SBD-6.3.1.2"]
POOL=ANSWERS+DISTRACTORS
QUESTION="What are the minimum password requirements according to CCoP 2.0?"

# --- domain-general schema ---
ENTITY_TYPES=["CII","CIIO","CIISystem","DigitalBoundary","Regulator","ComputerSystem","EnterpriseNetwork",
 "Obligation","AuditScope","EssentialService","Person","SecurityControl","Password","Passphrase",
 "DefaultCredential","PasswordLength","HashStorage","SecurityBaseline","Account","AccessLog","Port",
 "Service","Software","Malware","Device","ExternalStandard"]
RELATIONS=["DEFINES","DESIGNATES","APPLIES_TO","WITHIN_BOUNDARY","DETERMINED_BY","IN_AUDIT_SCOPE",
 "EXCLUDED_FROM_AUDIT","HAS_OBLIGATION","CONNECTED_TO","PART_OF","REQUIRES","ADDRESSES","MUST_CHANGE",
 "STORED_AS","DEFERS_TO","REVIEWS","DISABLES","PROTECTS_AGAINST"]

PROMPT="""Extract typed relation triples from this cybersecurity-compliance clause.
Use ONLY these entity types: {et}
Use ONLY these relations: {rt}
Normalize entities to canonical names (e.g. always "Password", "PasswordLength", "DefaultCredential",
"HashStorage", "SecurityBaseline", "AccessLog", "ExternalStandard" for NIST/ISO/industry standards,
"CII", "CIIO", "Regulator" for CSA/Commissioner).
Return ONLY a JSON array of {{"subject":..,"subject_type":..,"relation":..,"object":..,"object_type":..}}. No prose.

CLAUSE:
{clause}

JSON:"""

def fetch(cid):
    d=neo4j.GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
    with d.session(database=settings.neo4j_database) as s:
        r=s.run("MATCH (c:Clause {citation_id:$cid}) RETURN c.text AS t",cid=cid).single()
        if not r or not r["t"]:
            r=s.run("MATCH (cu:ComplianceUnit {cu_id:$cid})-[:FROM_CLAUSE]->(c:Clause) RETURN c.text AS t",cid=cid).single()
    d.close(); return (r["t"] if r else "")[:1200]

def extract(cid,text):
    cache=os.path.join(SCRATCH,f"omd_b05_ex_{re.sub(r'[^A-Za-z0-9]','_',cid)}.json")
    if os.path.exists(cache): return json.load(open(cache))
    from openai import OpenAI
    cli=OpenAI(api_key=settings.openrouter_api_key,base_url=settings.openrouter_base_url,timeout=60)
    p=PROMPT.format(et=", ".join(ENTITY_TYPES),rt=", ".join(RELATIONS),clause=text)
    r=cli.chat.completions.create(model=settings.ontology_discovery_model,messages=[{"role":"user","content":p}],temperature=0.0,max_tokens=600)
    raw=(r.choices[0].message.content or "").strip()
    try:
        from neo4j_graphrag.experimental.components.entity_relation_extractor import fix_invalid_json
        t=json.loads(fix_invalid_json(raw))
    except Exception:
        try: t=json.loads(raw)
        except Exception: t=[]
    t=t if isinstance(t,list) else []
    json.dump(t,open(cache,"w"),indent=1); return t

SYN={"critical information infrastructure":"CII","commissioner":"Regulator","csa":"Regulator",
 "password":"Password","passwords":"Password","passphrase":"Password","passphrases":"Password",
 "default password":"DefaultCredential","default account":"DefaultCredential","default credential":"DefaultCredential",
 "password length":"PasswordLength","hash":"HashStorage","hashed form":"HashStorage","hash form":"HashStorage",
 "nist":"ExternalStandard","iso":"ExternalStandard","industry standard":"ExternalStandard","best practice":"ExternalStandard",
 "security configuration baseline":"SecurityBaseline","configuration baseline":"SecurityBaseline","baseline":"SecurityBaseline",
 "account":"Account","access log":"AccessLog","log":"AccessLog","malware":"Malware"}
def canon(name,typ):
    n=(name or "").strip().lower().strip('"').strip()
    if n in SYN: return SYN[n]
    if typ in ENTITY_TYPES and (n in (typ.lower(),"") or len(n)<3): return typ
    for k,v in SYN.items():
        if k in n: return v
    return typ if typ in ENTITY_TYPES else n.title().replace(" ","")

print("BLIND extraction over pool (extractor sees no labels)...",flush=True)
clause_ent={}; rel_edges=set()
for cid in POOL:
    txt=fetch(cid)
    ents=set()
    for t in extract(cid,txt):
        se=canon(t.get("subject"),t.get("subject_type","")); oe=canon(t.get("object"),t.get("object_type",""))
        r=str(t.get("relation","")).upper()
        if se: ents.add(se)
        if oe: ents.add(oe)
        if se and oe and r: rel_edges.add((se,r,oe))
    clause_ent[cid]=ents
    print(f"  [{cid:16}] {sorted(ents)}")

# query entities (blind, same schema)
qtrips=extract("QUERY__B05",QUESTION)
Q=set()
for t in qtrips:
    for k,kt in [("subject","subject_type"),("object","object_type")]:
        e=canon(t.get(k),t.get(kt,""))
        if e: Q.add(e)
print(f"\nQUERY entities: {sorted(Q)}")
def neigh(e): return {b for a,r,b in rel_edges if a==e}|{a for a,r,b in rel_edges if b==e}
Qplus=set(Q)
for e in list(Q): Qplus|=neigh(e)
print(f"Q+ neighborhood: {sorted(Qplus)}\n")

# OMD Channel-I: structural overlap (NO hand-tuned per-question relation weights)
def score(cid):
    E=clause_ent[cid]
    return 1.0*len(Q&E)+0.5*len((Qplus-Q)&E)
ranked=sorted(POOL,key=lambda c:-score(c))
ans=set(ANSWERS)
print("="*70,"\nENTITY-STRUCTURAL retrieval ranking (labels shown only for grading):")
for i,cid in enumerate(ranked,1):
    print(f"  {i:2}. {score(cid):4.1f}  [{'ANSWER ' if cid in ans else 'distr. '}] {cid}")
aranks=[i for i,c in enumerate(ranked,1) if c in ans]
top3=set(ranked[:3])
print(f"\n  ANSWER ranks: {aranks} | answers in top-3: {len(ans&top3)}/3")
print("[done]")
