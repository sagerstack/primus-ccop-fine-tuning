# Doc 7 — Cybersecurity Act 2018 KG critique

Scope: high-value sections only (§7-9, §11-12, §14-16, §46, First Schedule ×11, Second Schedule.1).
Type validity (Φ) not re-checked — only groundedness, subject attribution, missed / wrong-relation triples.

| citation_id | category | issue | suggested-fix |
|---|---|---|---|
| ::SecondSchedule.1 | wrong-subject | Schedule defines *licensable services provided by third-party providers*; triples cast the **CIIO** as actor. `CIIO CONDUCTS PenetrationTesting` and `CIIO IMPLEMENTS Monitoring` misattribute the pen-test/SOC-monitoring *service* to the customer. | Re-subject to provider: `PenetrationTester CONDUCTS PenetrationTesting`; SOC-monitoring is a `ThirdParty` service, not CIIO `IMPLEMENTS Monitoring`. |
| ::SecondSchedule.1 | ungrounded | `ThirdParty HAS_CERTIFICATION Certification` — the Schedule is about *licensing*, says nothing about certification/credentials. | Drop, or replace with a licensable-service edge; optionally add `PenetrationTesting IDENTIFIES Vulnerability` (defined in the pen-test definition). |
| ::14 | missed | §14(2) "must establish such mechanisms and processes … for detecting cybersecurity threats and incidents" is not captured. | Add `CIIO IMPLEMENTS Monitoring` (and/or `Monitoring DETECTS CybersecurityThreat`). |
| ::15 | missed | §15(1)(a) auditor is "approved or appointed by the Commissioner" — no Regulator→Auditor edge. | Add `Regulator APPROVES Auditor` (or `APPOINTS Auditor`). |
| ::15 | missed | §15(2) owner must "furnish a copy of the report … to the Commissioner" — reporting edge absent. | Add `CIIO REPORTS Regulator`. |
| ::8 | wrong-relation | §8 is *pre-designation information-gathering* to ascertain CII criteria; no designation occurs. `Regulator DESIGNATES ComputerSystem` overstates the clause. | Weaken/drop; §8 has no clean relation (info-gathering power) — leave thin rather than mislabel. |
| ::9 | wrong-relation (minor) | §9 is *withdrawal* of designation; `Regulator DESIGNATES CII` asserts the opposite act. No anti-relation exists, so borderline. | Acceptable as domain link; note the polarity mismatch. |
| ::16 | wrong-subject (minor) | Act §16 has the **Commissioner** conduct exercises and the owner *participate*; `CIIO CONDUCTS CybersecurityExercise` inverts the Act actor (though CCoP §7.3 does put exercises on CIIOs). | Keep if intentionally CCoP-aligned; otherwise the Act actor is the Regulator (no CONDUCTS domain for Regulator → thin). |

## Summary
High-value core is largely sound: §11 (ISSUES/GRANTS/WAIVES), §12, §46 (EXEMPTS), and all 11 First-Schedule sectors (uniform `EssentialService IN_SECTOR Sector` + `CII DELIVERS EssentialService`) are correct and complete.
The one real problem cluster is **Second Schedule.1**, where all three triples are mis-subjected (CIIO instead of the licensed third-party provider) or ungrounded (certification); §14(2) detection and §15 auditor-approval/reporting are genuine misses.
