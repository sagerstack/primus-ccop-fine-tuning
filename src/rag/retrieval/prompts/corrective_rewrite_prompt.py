"""CRAG-style corrective query rewrite prompt for graphont-agentic mode.

Rewrites the original compliance question into a retrieval query using the
corpus's canonical vocabulary (from concept_aliases.json) without asserting
a verdict. Used ONLY in Incorrect/Ambiguous routes (Round-2 corrective).
"""

PROMPT_VERSION = "v1"

# Canonical vocabulary glossary generated from concept_aliases.json (40 concepts
# with lay-synonym surface forms). Prefer these corpus phrases over colloquial
# terms to improve dense-channel embedding match.
_GLOSSARY = """Account; account; user account
CII; a CII; cii asset; cii system; critical information infrastructure; the CII
CII owner; CIIO; owner of a critical information infrastructure; the organisation
CISA; CREST; CRISC; Certification
CCoP; CCoP 2.0; CodeOfPractice; the Code
ComputerSystem; computer; computer system
Cryptography; cryptographic key; encryption; hash
CyberThreatActor; adversary; attacker; threat actor
DNSSEC; dns security extension; dnssec
DefaultCredential; default account; default credential; default password
DigitalBoundary; cyber operating environment; digital boundary; perimeter boundary; trust boundary
EnterpriseNetwork; corporate network; enterprise network
ExternalStandard; ISO; NIST; OWASP; best practice; industry standard
HashStorage; hash; hash form; hashed form
IT system; ITSystem; information technology
CIRT; IncidentResponseTeam
Cybersecurity Act 2018; Legislation; the Act
OT CII; OT system; OTSystem; operational technology
Password; passphrase; password
PasswordLength; password length
Port; port
CSA; Commissioner; Cyber Security Agency; Regulator; Sector Lead
SecurityConfigurationBaseline; baseline; configuration baseline; security configuration baseline
SecurityControl; control; measure; mechanism; security measure
Service; service
ThirdParty; external party; service provider; vendor
authenticate; authentication
authorisation; authorization
defence by diversity; defence-by-diversity; defense by diversity
defence in depth; defence-in-depth; defense in depth
ids/ips; intrusion detection; intrusion prevention; intrusion-detection; nids; nips
least privilege; least-privilege; minimum extent of access; minimum privilege
2fa; mfa; multi-factor authentication; multi-factor-authentication; multifactor; two-factor authentication
network segment; network segmentation; network-segmentation; segment the network
administrative access; pam; privileged access; privileged account; privileged-access-management
segregation of duties; segregation-of-duties; separation of duties
log-on; logon session; session management; session-management
data diode; one-way data flow; unidirectional gateway; unidirectional-gateway
waf; web application firewall; web-application-firewall
zero trust; zero-trust"""

SYSTEM_PROMPT = f"""You rewrite a compliance question into a SEARCH QUERY for retrieval over Singapore's CCoP 2.0 regulatory corpus. Your output is used ONLY for retrieval — NOT to answer the question.

Prefer the corpus's canonical phrases when the question implies them:
{_GLOSSARY}

RULES:
1. Preserve EVERY concrete element from the question (entity names, systems, scenarios, thresholds, values).
2. Add canonical vocabulary ONLY where clearly implied by the question's meaning.
3. Do NOT answer the question, conclude, or imply a compliance verdict (e.g., do NOT output "must comply" / "not in scope" / "exempt" / "is required" / "prohibited").
4. Do NOT invent clause numbers, section references, thresholds, or values not present in the original question.
5. NEUTRALITY: the query must be valid whether the true answer is YES or NO. The rewrite should help retrieve clauses that SUPPORT EITHER OUTCOME.
6. Avoid generic filler ("compliance requirements", "best practices", "security measures") unless the question itself is generic.

OUTPUT — JSON only, ≤3 keyphrases:
{{"keyphrases": ["...", "...", "..."], "search_query": "phrase; phrase; phrase"}}

The "search_query" should be a semicolon-separated list of ~2-4 short retrieval phrases (NOT a grammatical sentence). Each phrase should use canonical vocabulary where applicable and focus on the concrete scenario + the regulatory aspect being asked.

EXAMPLES:

Q: A hospital's MRI and patient-monitoring systems are designated CII; the admin system shares the same enterprise network. Does CCoP 2.0 mandatory compliance extend to the admin system?
A: {{"keyphrases": ["digital boundary of designated CII versus enterprise network", "system sharing enterprise network with designated CII", "cyber operating environment of critical information infrastructure"], "search_query": "digital boundary of designated CII; system sharing enterprise network with CII; cyber operating environment"}}

Q: How long must passwords be under CCoP 2.0?
A: {{"keyphrases": ["password length", "password requirement"], "search_query": "password length; password requirement; authentication access control"}}

Q: Our OT CII network has a one-way data flow to the corporate network for monitoring. Is physical segregation still required?
A: {{"keyphrases": ["OT CII network segregation", "one-way data flow / unidirectional gateway", "physical segregation with data diode"], "search_query": "OT CII network segregation; unidirectional gateway; data diode; physical segregation"}}"""

USER_PROMPT_TEMPLATE = """Rewrite this compliance question into a retrieval query using the canonical vocabulary where applicable. Output JSON only.

QUESTION: {question}"""


def build_rewrite_prompt(question: str) -> list[dict]:
    """Build the messages list for the corrective rewrite LLM call."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": USER_PROMPT_TEMPLATE.format(question=question)},
    ]


__all__ = ["PROMPT_VERSION", "build_rewrite_prompt"]
