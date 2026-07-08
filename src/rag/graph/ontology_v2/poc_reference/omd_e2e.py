"""E2E: feed the OMD-retrieved top clauses for B01-001 to primus (real generate
node), print the exact context + response.
cd src && poetry run python <this>
"""
import os, json, re
S=os.path.dirname(os.path.abspath(__file__))
from infrastructure.config.settings import get_settings
settings=get_settings()
import neo4j
from langchain_core.documents import Document
from rag.retrieval.nodes.generation import generate_response

QUESTION=("A healthcare provider's patient monitoring systems and MRI machines have been designated as CII. "
 "Their hospital administration system (patient records, billing, appointments) shares the same enterprise network. "
 "Does CCoP 2.0 mandatory compliance extend to the hospital administration system?")

# --- recompute OMD relational ranking from cached extraction ---
ANSWERS=["CCoP-1.4.1","CCoP-1.2.1#CII","Act-7","RtF-2.2","RtF-2.3"]
DISTR=["Act-14","Act-15","Act-16","Act-10","Act-11","CCoP-1.3.2","CCoP-10.2.1","CCoP-10.2.2","CCoP-10.2.3","SBD-6.6.1.2","SBD-6.6.1.3","CCoP-5.13.2","CCoP-5.15.2"]
W={"APPLIES_TO":2,"DETERMINED_BY":2,"EXCLUDED_FROM_AUDIT":2,"WITHIN_BOUNDARY":1,"DEFINES":1,"DESIGNATES":1,
   "IN_AUDIT_SCOPE":-1.5,"NOTIFIES":-1.5,"HAS_OBLIGATION":-0.5}
def rels(cid):
    f=f"{S}/omd_ex_{re.sub(r'[^A-Za-z0-9]','_',cid)}.json"
    return [str(t.get('relation','')).upper() for t in (json.load(open(f)) if os.path.exists(f) else [])]
ranked=sorted(ANSWERS+DISTR, key=lambda c:-sum(W.get(r,0) for r in rels(c)))
TOPK=ranked[:6]
print("OMD top-6 passed to primus:", TOPK, "\n")

# --- fetch verbatim texts ---
d=neo4j.GraphDatabase.driver(settings.neo4j_uri,auth=(settings.neo4j_user,settings.neo4j_password))
texts={}
with d.session(database=settings.neo4j_database) as s:
    for cid in TOPK:
        r=s.run("MATCH (c:Clause {citation_id:$cid}) RETURN c.text AS t, c.source_doc AS sd",cid=cid).single()
        if not r or not r["t"]:
            r=s.run("MATCH (cu:ComplianceUnit {cu_id:$cid})-[:FROM_CLAUSE]->(c:Clause) RETURN c.text AS t, c.source_doc AS sd",cid=cid).single()
        texts[cid]=(r["t"], r["sd"]) if r else ("","")
d.close()

# --- build filtered_documents (graphcpl-style) ---
def src_name(cid):
    if cid.startswith("RtF"): return "CCoP Response to Feedback"
    if cid.startswith("Act"): return "Cybersecurity Act 2018"
    return "CCoP 2.0"
docs=[]
for i,cid in enumerate(TOPK):
    txt,sd=texts[cid]
    docs.append(Document(page_content=(txt or "").strip(),
        metadata={"citation_id":cid,"document_source":src_name(cid),"section":"OMD-retrieved",
                  "similarity_score":1.0-0.01*i}))

state={"mode":"graphcpl","query":QUESTION,"rewritten_query":"","needs_retrieval":True,
 "documents":docs,"filtered_documents":docs,"grading_scores":[],"retrieval_succeeded":True,
 "retrieval_attempts":1,"reranker_scores":[],"generation":"","is_rag_augmented":True,"citations":[],
 "error":"","system_prompt":"","user_prompt":"","prompt_tokens":0,"completion_tokens":0,
 "total_tokens":0,"latency_ms":0,"retrieved_contexts_detailed":[]}

print("calling primus (generate node)...\n",flush=True)
state=generate_response(state)

print("="*90); print("SYSTEM PROMPT"); print("="*90)
print(state.get("system_prompt","")[:1500])
print("\n"+"="*90); print(f"USER PROMPT (context sent to primus) — {len(state.get('user_prompt',''))} chars"); print("="*90)
print(state.get("user_prompt",""))
print("\n"+"="*90); print("PRIMUS RESPONSE"); print("="*90)
print(state.get("generation",""))
print("\n"+"="*90)
print(f"tokens: prompt={state.get('prompt_tokens')} completion={state.get('completion_tokens')} latency={state.get('latency_ms')}ms")
print("GT expected_label: not-applicable (compliance does NOT auto-extend to the shared-network admin system)")
