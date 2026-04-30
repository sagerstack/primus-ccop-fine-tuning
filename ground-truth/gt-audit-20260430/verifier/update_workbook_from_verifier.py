from __future__ import annotations

import json
import re
import shutil
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZIP_DEFLATED, ZipFile
import xml.etree.ElementTree as ET


NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS = {"a": NS_MAIN}
ET.register_namespace("", NS_MAIN)

ROOT = Path(__file__).resolve().parents[3]
WORKBOOK_PATH = ROOT / "ground-truth" / "expert-validation" / "CCoP_V2_Test_Cases_Expert_Review.xlsx"
AUDIT_PATH = ROOT / "ground-truth" / "gt-audit-20260430" / "audit_defects.json"
DECISIONS_PATH = ROOT / "ground-truth" / "gt-audit-20260430" / "verifier" / "audit_verifier_decisions.json"
BACKUP_PATH = ROOT / "ground-truth" / "expert-validation" / "CCoP_V2_Test_Cases_Expert_Review.pre-verifier-20260430.xlsx"

FIELD_TO_COL = {
    "Test ID": "A",
    "Benchmark": "B",
    "Sector": "C",
    "Domain": "D",
    "Difficulty": "E",
    "Category": "F",
    "CCoP Section": "G",
    "Clause Refs": "H",
    "Question": "I",
    "Expected Label": "J",
    "Expected Response": "K",
    "Key Facts (Critical)": "L",
    "Key Facts (Important/Supporting)": "M",
    "Reasoning Chain": "N",
    "Forbidden Claims": "O",
    "Approved (Y/N)": "P",
    "Accuracy (1-5)": "Q",
    "Completeness (1-5)": "R",
    "Remarks": "S",
}

DIRECT_PREFIXES = (
    "**Prioritized",
    "According",
    "A ",
    "An ",
    "The ",
    "This ",
    "Under ",
    "Cloud-provider",
    "Two ",
    "24-hour",
    "12-month",
    "8-hour",
    "CCoP ",
    "Cybersecurity ",
)


def natural_key(value: str):
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", value)]


def extract_text(cell: ET.Element | None) -> str:
    if cell is None:
        return ""
    cell_type = cell.attrib.get("t")
    if cell_type == "inlineStr":
        return "".join(t.text or "" for t in cell.iterfind(".//a:t", NS))
    value = cell.find("a:v", NS)
    if value is not None and value.text is not None:
        return value.text
    return ""


def set_inline_text(cell: ET.Element, text: str) -> None:
    ref = cell.attrib["r"]
    style = cell.attrib.get("s")
    cell.clear()
    cell.attrib["r"] = ref
    if style is not None:
        cell.attrib["s"] = style
    cell.attrib["t"] = "inlineStr"
    is_el = ET.SubElement(cell, f"{{{NS_MAIN}}}is")
    t_el = ET.SubElement(is_el, f"{{{NS_MAIN}}}t")
    if text.startswith(" ") or text.endswith(" ") or "\n" in text:
        t_el.attrib["{http://www.w3.org/XML/1998/namespace}space"] = "preserve"
    t_el.text = text


def get_or_create_cell(row: ET.Element, col: str) -> ET.Element:
    row_idx = row.attrib["r"]
    target_ref = f"{col}{row_idx}"
    for cell in row.findall("a:c", NS):
        if cell.attrib.get("r") == target_ref:
            return cell
    new_cell = ET.Element(f"{{{NS_MAIN}}}c", {"r": target_ref, "t": "inlineStr"})
    cells = row.findall("a:c", NS)
    inserted = False
    for idx, cell in enumerate(cells):
        if col_to_num(cell_ref_to_col(cell.attrib["r"])) > col_to_num(col):
            row.insert(idx, new_cell)
            inserted = True
            break
    if not inserted:
        row.append(new_cell)
    set_inline_text(new_cell, "")
    return new_cell


def cell_ref_to_col(ref: str) -> str:
    return re.match(r"[A-Z]+", ref).group(0)


def col_to_num(col: str) -> int:
    total = 0
    for ch in col:
        total = total * 26 + (ord(ch) - ord("A") + 1)
    return total


def normalize_instruction_prefix(text: str) -> str:
    lowered = text.strip()
    for prefix in ("Update Expected Response: ", "Update Expected Response/Reasoning Chain: ", "Update Reasoning Chain: "):
        if lowered.startswith(prefix):
            return lowered[len(prefix):]
    return lowered


def extract_quoted(text: str) -> list[str]:
    return re.findall(r"'([^']*)'", text)


def apply_instruction(current: str, instruction: str) -> str | None:
    text = normalize_instruction_prefix(instruction.strip())

    if not text:
        return current

    if text.startswith("Replace with:") or text.startswith("Update to:"):
        quoted = extract_quoted(text)
        if quoted:
            return quoted[-1]
        tail = text.split(":", 1)[1].strip()
        return tail

    if text.startswith("Add:"):
        quoted = extract_quoted(text)
        if len(quoted) == 1:
            addition = quoted[0]
            if not current:
                return addition
            if addition in current:
                return current
            return current.rstrip() + ("; " if not current.rstrip().endswith(";") else " ") + addition

    if "30 days before audit submission" in text:
        quoted = extract_quoted(text)
        if quoted:
            new_sentence = quoted[-1]
            updated = re.sub(
                r"[^.\n]*30 days before audit submission[^.\n]*\.",
                new_sentence,
                current,
                count=1,
            )
            if updated != current:
                return updated

    if text.startswith("Replace the trailing ") and "Reference:" in text:
        quoted = extract_quoted(text)
        if quoted:
            new_ref = quoted[-1]
            updated = re.sub(r"Reference:[^\n]*$", new_ref, current, count=1, flags=re.MULTILINE)
            if updated != current:
                return updated

    if text.startswith("replace the 'CCoP Domain: "):
        quoted = extract_quoted(text)
        if len(quoted) >= 4:
            new_domain = quoted[1]
            new_ref = quoted[3]
            domain_payload = new_domain.replace("CCoP Domain: ", "")
            updated = re.sub(
                r"(\*\*CCoP Domain:\*\*|CCoP Domain:)[^\n]*",
                f"**CCoP Domain:** {domain_payload}",
                current,
                count=1,
            )
            updated = re.sub(r"Reference:[^\n]*$", new_ref, updated, count=1, flags=re.MULTILINE)
            if updated != current:
                return updated

    if text.startswith("Replace the specific-hours bullet with:"):
        quoted = extract_quoted(text)
        if quoted:
            new_line = quoted[-1]
            updated = re.sub(r"[^\n]*(2 hours|24 hours|2-hour|24-hour)[^\n]*", new_line, current, count=1)
            if updated != current:
                return updated

    if text.startswith("Replace the §10.2.3 sentence with:"):
        quoted = extract_quoted(text)
        if quoted:
            new_sentence = quoted[-1]
            updated = re.sub(r"[^.]*10\.2\.3[^.]*\.", new_sentence, current, count=1)
            if updated != current:
                return updated

    if text.startswith("Replace the sentence with:"):
        quoted = extract_quoted(text)
        if quoted:
            new_sentence = quoted[-1]
            updated = re.sub(r"[^.]*Section 11 states[^.]*\.", new_sentence, current, count=1)
            if updated != current:
                return updated

    if text.startswith(DIRECT_PREFIXES):
        return text

    if text.startswith("Replace ") or text.startswith("replace "):
        parts = re.split(r"\bwith\b", text, maxsplit=1)
        if len(parts) == 2:
            old_part, new_part = parts
            olds = extract_quoted(old_part)
            news = extract_quoted(new_part)
            if olds and news and len(olds) == len(news):
                updated = current
                for old, new in zip(olds, news):
                    updated = updated.replace(old, new)
                if updated != current:
                    return updated

    if text.startswith("Change "):
        parts = re.split(r"\bto\b", text, maxsplit=1)
        if len(parts) == 2:
            olds = extract_quoted(parts[0])
            news = extract_quoted(parts[1])
            if olds and news and len(olds) == len(news):
                updated = current
                for old, new in zip(olds, news):
                    updated = updated.replace(old, new)
                if updated != current:
                    return updated

    if text.startswith("Drop the "):
        olds = extract_quoted(text)
        if len(olds) == 1:
            return current.replace(olds[0], "")

    return None


def should_set_direct(field: str, value: str) -> bool:
    if field in {
        "Domain",
        "CCoP Section",
        "Clause Refs",
        "Expected Label",
        "Key Facts (Critical)",
        "Key Facts (Important/Supporting)",
        "Reasoning Chain",
    }:
        return True
    if field == "Forbidden Claims":
        return not value.startswith("Add:")
    if field == "Question":
        return not value.startswith("Replace ")
    if field == "Expected Response":
        if value.startswith(DIRECT_PREFIXES):
            return True
        if value.startswith(("Replace ", "Update ", "Change ", "Drop ", "Reframe ", "Anchor ", "Use ")):
            return False
        return True
    return False


def load_sheet_xml():
    with ZipFile(WORKBOOK_PATH) as zf:
        sheet_xml = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))
        all_files = [(name, zf.read(name)) for name in zf.namelist()]
    return sheet_xml, all_files


def build_row_map(sheet_root: ET.Element) -> dict[str, ET.Element]:
    row_map = {}
    sheet_data = sheet_root.find("a:sheetData", NS)
    for row in sheet_data.findall("a:row", NS):
        test_id = extract_text(get_or_create_cell(row, "A")).strip()
        if test_id and test_id != "Test ID":
            row_map[test_id] = row
    return row_map


def load_data():
    audit = json.loads(AUDIT_PATH.read_text())
    decisions = json.loads(DECISIONS_PATH.read_text())
    decision_map = {d["defect_id"]: d for d in decisions if "-M" not in d["defect_id"]}
    return audit, decision_map


def apply_change_to_field(row: ET.Element, field: str, new_value: str) -> tuple[bool, str]:
    if field not in FIELD_TO_COL:
        return False, f"unsupported field {field}"

    cell = get_or_create_cell(row, FIELD_TO_COL[field])
    current = extract_text(cell)

    if should_set_direct(field, new_value):
        set_inline_text(cell, new_value)
        return True, "direct"

    transformed = apply_instruction(current, new_value)
    if transformed is not None:
        set_inline_text(cell, transformed)
        return True, "transformed"

    return False, "manual"


ROW_FIELD_NAMES = [
    "Test ID",
    "Benchmark",
    "Sector",
    "Domain",
    "Difficulty",
    "Category",
    "CCoP Section",
    "Clause Refs",
    "Question",
    "Expected Label",
    "Expected Response",
    "Key Facts (Critical)",
    "Key Facts (Important/Supporting)",
    "Reasoning Chain",
    "Forbidden Claims",
    "Approved (Y/N)",
    "Accuracy (1-5)",
    "Completeness (1-5)",
    "Remarks",
]

B13_DOMAIN_MAP = {
    "1": "Applicability",
    "3": "Governance",
    "4": "Identification",
    "5": "Protection",
    "7": "Response",
    "9": "Training",
}


def get_row_values(row: ET.Element) -> dict[str, str]:
    return {field: extract_text(get_or_create_cell(row, col)).strip() for field, col in FIELD_TO_COL.items()}


def apply_override_changes(row: ET.Element, changes: list[tuple[str, str]]) -> bool:
    for field, value in changes:
        ok, _ = apply_change_to_field(row, field, value)
        if not ok:
            return False
    return True


def replace_reference_line(text: str, reference_line: str) -> str:
    if "Reference:" in text:
        return re.sub(r"Reference:[^\n]*", reference_line, text, count=1)
    return text.rstrip() + "\n\n" + reference_line


def replace_first(text: str, old: str, new: str) -> str:
    if old in text:
        return text.replace(old, new, 1)
    return text


def rewrite_b04_expected_response(current: str) -> str:
    updated = current
    replacements = [
        (
            "Based on CCoP 2.0 Section 10 definitions:",
            "Based on the CCoP 2.0 §1.2.1 OT definition and §10.1.1 OT-CII scope:",
        ),
        (
            "This is a hybrid IT/OT system under CCoP 2.0.",
            "Under CCoP 2.0 §1.2.1 and §10.2.1, this is a mixed IT/OT environment whose OT components must be distinguished from connected IT components.",
        ),
        (
            "CCoP 2.0 Section 10 applies to systems that monitor and control physical processes.",
            "Under CCoP 2.0 §1.2.1 and §10.1.1, systems that monitor and/or control physical processes are treated as OT.",
        ),
        (
            "CCoP 2.0 Section 10 applies to bedside sensors and has implications for alerting systems. Section 5 applies to display systems and EHR storage.",
            "Under CCoP 2.0 §1.2.1, the bedside sensors are the clearest OT component; connected display, alerting and record-storage systems remain IT or hybrid components that must be secured consistently with the OT boundary and the applicable Section 5 controls.",
        ),
    ]
    for old, new in replacements:
        updated = replace_first(updated, old, new)

    updated = updated.replace("per Section 10.2.3", "under §10.2.1 and, where relevant, §10.2.3")
    updated = updated.replace("Section 10.2.3", "§10.2.3")
    updated = updated.replace("Section 10.1", "§10.1")
    updated = updated.replace("Section 10", "§10")
    updated = updated.replace("Section 5 applies", "Section 5 controls apply")
    updated = updated.replace("Section 5 (IT security)", "Section 5 controls for the IT-side components")
    updated = updated.replace("Section 10 (OT security)", "Section 10 controls for the OT-side components")
    updated = updated.replace("CCoP 2.0 Section 10 recognizes that modern critical infrastructure systems increasingly blend IT and OT capabilities.", "CCoP 2.0 recognises OT by function in §1.2.1 and requires the OT-side architecture and boundaries to be secured in §10.2.")
    return updated


def rewrite_b12_expected_response(values: dict[str, str]) -> str:
    current = values["Expected Response"]
    refs = values["Clause Refs"]
    updated = re.sub(r"under CCoP 2\.0 [^,\n]+", f"against CCoP 2.0 {refs}", current, count=1)
    return replace_reference_line(updated, f"Reference: CCoP 2.0 {refs}; CSA Guidelines for Auditing CII.")


def rewrite_b12_reasoning(values: dict[str, str]) -> str:
    current = values["Reasoning Chain"]
    refs = values["Clause Refs"]
    updated = re.sub(r"Determine CCoP clause(?:s)?: [^;]+", f"Determine CCoP clause(s): {refs}", current, count=1)
    if updated == current and refs not in current:
        updated = current.rstrip("; ") + f"; Determine CCoP clause(s): {refs}"
    return updated


def rewrite_b13_generic(values: dict[str, str]) -> str:
    current = values["Expected Response"]
    section = values["CCoP Section"]
    refs = values["Clause Refs"]
    domain = B13_DOMAIN_MAP.get(section, values["Domain"] or "CCoP")
    updated = re.sub(r"\*\*CCoP Domain:\*\*[^\n]*", f"**CCoP Domain:** {domain} (Section {section})", current, count=1)
    return replace_reference_line(
        updated,
        f"Reference: CCoP 2.0 {refs}; Cybersecurity Act 2018 §15 (audit obligation); CCoP 2.0 §2.1 (Remediation of Audit Findings); CSA's Guidelines for Auditing CII §6.5, §6.7 and §7.4.",
    )


def b13_016_override() -> list[tuple[str, str]]:
    response = """**Evidence Requirements for: Physical security implementation**

**CCoP Domain:** Governance (Section 3)

CCoP 2.0 does not prescribe a standalone physical-security control catalogue in the audited corpus. A grounded answer should therefore focus on evidence that the CIIO has defined, implemented and reviewed its own policies and procedures for protecting the CII environment, rather than claiming that camera maps, guard tours or badge logs are themselves mandated by a specific CCoP clause.

**Relevant Evidence Types:**
- CIIO policy or procedure covering facility or physical access controls relevant to the CII
- Access authorisation and review records for protected areas
- Exception or incident records showing how deviations were handled
- Evidence that the documented controls are implemented and periodically reviewed

Reference: CCoP 2.0 §3.3.1; Cybersecurity Act 2018 §15 (audit obligation); CSA's Guidelines for Auditing CII §6.5, §6.7 and §7.4."""
    return [
        ("Clause Refs", "3.3.1 (CIIO-defined policies only)"),
        ("Expected Response", response),
        ("Key Facts (Critical)", "The CIIO's own policies and procedures define how facility or physical access controls are managed for the CII; evidence should show those controls are implemented and reviewed."),
        ("Key Facts (Important/Supporting)", "Physical-security artefacts may be useful supporting evidence, but they should not be presented as CCoP-prescribed controls unless the corpus expressly requires them."),
    ]


def b13_019_override() -> list[tuple[str, str]]:
    response = """**Evidence Requirements for: Forensic investigation readiness**

**CCoP Domain:** Response (Section 7)

The grounded CCoP obligations here are the documented Cybersecurity Incident Response Team structure and the requirement to perform post-incident root-cause analysis. CCoP 2.0 does not itself require a forensic retainer, a chain-of-custody procedure template or a tool inventory as standalone CIIO obligations.

**Relevant Evidence Types:**
- Incident response plan sections that define CIRT roles and responsibilities
- Root-cause analysis records for completed incidents
- Procedures used to collect and preserve digital forensic evidence during incidents
- Evidence that corrective actions are tracked after each post-incident review

Reference: CCoP 2.0 §7.1.1, §7.1.4; Cybersecurity Act 2018 §15 (audit obligation); CSA's Guidelines for Auditing CII §6.5, §6.7 and §7.4."""
    return [
        ("Clause Refs", "7.1.1; 7.1.4"),
        ("Expected Response", response),
        ("Key Facts (Critical)", "Root-cause analysis records exist for each incident (per §7.1.4); CIRT roles and responsibilities are documented (per §7.1.1)."),
        ("Key Facts (Important/Supporting)", "Forensic tooling or external specialist arrangements may support the CIIO's response process, but they are not themselves explicit CCoP 2.0 obligations in the audited corpus."),
    ]


def b01_013_override() -> list[tuple[str, str]]:
    return [
        (
            "Expected Response",
            "CCoP 2.0 applies to the designated CII and the cyber operating environment defined for that CII. The passenger information system is not automatically in scope just because it exchanges data with the signalling system, but the interface and any dependency that can affect the signalling CII must be assessed and secured. The CIIO should determine whether the passenger information system forms part of the signalling system's cyber operating environment or creates a risk path into the designated CII and, if the designation or scope documents are unclear, confirm the scope with CSA. Reference: CCoP 2.0 §1.2.1, §1.4.1; Cybersecurity Act 2018 §7.",
        ),
        (
            "Key Facts (Critical)",
            "CCoP 2.0 applies to the designated CII and its cyber operating environment, not to every non-designated system in the organisation by default; interfaces and dependencies that can affect the CII must still be assessed and secured.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "A non-designated feeder system may remain outside direct designation scope, but its connection into the CII can still require control and risk treatment; unresolved scope questions should be checked against the designation records and, if needed, with CSA.",
        ),
        (
            "Reasoning Chain",
            "Identify the designated CII and its cyber operating environment; assess whether the connected non-designated system forms part of that environment or creates a risk path into the CII; apply the resulting scope and control obligations.",
        ),
    ]


def b01_015_override() -> list[tuple[str, str]]:
    return [
        (
            "Expected Response",
            "Yes, the connection should be segmented or otherwise tightly controlled to protect the broadcast CII. The key point is not that the news production system automatically becomes in-scope CII, but that §5.5 and §5.1.2 require the CIIO to secure network connectivity to and from the CII and to control access between parts of the environment commensurate with risk. If the news production system shares a network path with the broadcast CII, the CIIO should separate the networks or enforce controlled access points that restrict and monitor traffic into the broadcast environment. Reference: CCoP 2.0 §5.5, §5.1.2.",
        ),
        (
            "Key Facts (Critical)",
            "Network security obligations apply to connectivity into and out of the CII even when the other system is not itself designated CII; segmentation or equally strong access controls are needed where shared network paths create risk to the CII.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "The objective is to protect the broadcast CII boundary with controlled and monitored access paths rather than to treat every content-production system as automatically in scope.",
        ),
        (
            "Reasoning Chain",
            "Determine whether the non-designated system shares network connectivity with the CII; apply the CII-facing network-security and access-control obligations; choose segmentation or equivalent controlled access measures to reduce pivot risk into the CII.",
        ),
    ]


def b02_013_override() -> list[tuple[str, str]]:
    return [
        (
            "Expected Response",
            "Yes. The described controls are consistent with a strong PAM implementation under CCoP 2.0. Individual named privileged accounts satisfy the accountability requirement, while session recording and monitoring can be used to support the access logging obligations in §6.1.1 and the retention and protection obligations in §6.1.4. The just-in-time approval model is not specifically mandated, but it is consistent with the objective of tightly controlling privileged access. Reference: CCoP 2.0 §5.3.1, §6.1.1, §6.1.4.",
        ),
        (
            "Key Facts (Critical)",
            "Privileged access should be attributable to named individuals; access logging and session evidence must be retained and protected in accordance with the logging controls.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "A just-in-time approval workflow is a stronger implementation choice, but the grounded CCoP anchors are the PAM control plus the logging, retention and protection clauses.",
        ),
        (
            "Reasoning Chain",
            "Confirm that privileged accounts are individually attributable; verify that access activity is logged and the resulting records are retained and protected; assess whether the access-approval workflow strengthens control over privileged use.",
        ),
    ]


def b02_015_override() -> list[tuple[str, str]]:
    return [
        (
            "Expected Response",
            "No. ISO 27001 certification does not by itself satisfy CCoP 2.0 compliance. The CCoP has legal force under the Cybersecurity Act and applies specifically to the designated CII, while ISO 27001 is a separate framework that may overlap with some controls but does not replace the statutory obligation to comply with the Code and to undergo the required cybersecurity audit process. A CIIO may reuse ISO-aligned controls as evidence where they satisfy the Code, but it still needs to demonstrate compliance with the CCoP on its own terms. Reference: Cybersecurity Act 2018 §11, §15.",
        ),
        (
            "Key Facts (Critical)",
            "The CCoP is a legal obligation for designated CII under the Cybersecurity Act and is not displaced by certification against a different framework.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "ISO 27001 controls may overlap with CCoP controls, but the CIIO still has to evidence compliance with the Code and its audit obligations specifically.",
        ),
        (
            "Reasoning Chain",
            "Separate the legal status of the CCoP from the voluntary or parallel status of ISO 27001; determine whether the CIIO can evidence the Code's own obligations; do not assume ISO certification substitutes for the CII-specific compliance and audit regime.",
        ),
    ]


def b01_001_override() -> list[tuple[str, str]]:
    return [
        (
            "Expected Response",
            "CCoP 2.0 mandatory compliance applies to the designated CII and the cyber operating environment defined for that CII, not automatically to every system on the same enterprise network. The hospital administration system does not become in-scope solely because it shares network infrastructure with the patient-monitoring and MRI CII. However, if it forms part of the cyber operating environment of the designated CII or creates a path that can affect the CII, the interface and related dependencies must be assessed and secured. Reference: CCoP 2.0 §1.2.1, §1.4.1; Cybersecurity Act 2018 §7.",
        ),
        (
            "Key Facts (Critical)",
            "Designation scope is tied to the CII and its cyber operating environment, not the whole enterprise network by default.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "Shared infrastructure or connectivity can still require control and risk treatment where it creates a path that can affect the designated CII.",
        ),
        (
            "Reasoning Chain",
            "Identify the designated CII and its cyber operating environment; determine whether the connected enterprise system is within that environment or creates a path that can affect the CII; apply scope and control obligations accordingly.",
        ),
    ]


def b01_006_override() -> list[tuple[str, str]]:
    return [
        ("CCoP Section", "Outside audited corpus - 2024 amendment regime"),
        ("Clause Refs", "Out of corpus for this GT: 2024 amendment materials not included in the audited CCoP corpus"),
        (
            "Expected Response",
            "The audited corpus used for this GT does not contain the 2024 amendment materials needed to give a source-backed answer on ESCI, STCC or FDI obligations. A grounded answer for this dataset is therefore that CCoP 2.0 governs designated CII under the current Cybersecurity Act / CCoP corpus, while any STCC-specific obligations would need to be answered from the amendment Act and any related CSA materials that are not part of this corpus.",
        ),
        (
            "Key Facts (Critical)",
            "The 2024 amendment categories are outside the audited corpus and cannot be answered from CCoP 2.0 alone.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "Do not assume that STCC obligations are identical to the current CII obligations without the amendment materials in scope.",
        ),
        (
            "Reasoning Chain",
            "Check whether the source corpus contains the 2024 amendment regime; if it does not, explicitly limit the answer to what the current CCoP corpus covers and avoid inventing STCC obligations.",
        ),
    ]


def b01_021_override() -> list[tuple[str, str]]:
    return [
        ("CCoP Section", "7"),
        ("Clause Refs", "7.1.1(b) [support: Cybersecurity Act 2018 §14]"),
        (
            "Expected Response",
            "A ransomware incident affecting only the non-designated research database does not automatically trigger the CII incident-reporting obligation just because the organisation also operates designated CII. The grounded question is whether the incident affects, or creates a risk of affecting, the designated clinical management CII. The CIIO should assess the connectivity and potential impact on the designated CII, activate the incident-response process as needed, and ensure that the incident-reporting structure in the IR plan complies with the Cybersecurity Act and other applicable laws. Reference: CCoP 2.0 §7.1.1(b); Cybersecurity Act 2018 §14.",
        ),
        (
            "Key Facts (Critical)",
            "The CII reporting obligation is tied to incidents affecting the designated CII or its incident-reporting structure, not every incident in the wider organisation.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "A non-designated incident still requires assessment for spillover risk into the designated CII and may trigger other legal obligations outside the CCoP.",
        ),
        (
            "Reasoning Chain",
            "Determine whether the incident affects or could affect the designated CII; apply the IR-plan reporting structure accordingly; avoid unsupported numeric deadlines in the CCoP answer.",
        ),
    ]


def b02_018_override() -> list[tuple[str, str]]:
    return [
        ("CCoP Section", "4 and 10"),
        ("Clause Refs", "4 (risk assessment / threat modelling), 10.1.1"),
        (
            "Expected Response",
            "No. OT CII remains subject to the general CCoP obligations unless a specific clause says otherwise, and Section 10 supplements those obligations rather than exempting OT CII from them wholesale. If threat modelling is part of the applicable risk-assessment expectations for the CII, the OT team cannot reject it simply by labelling it an IT-only practice.",
        ),
        (
            "Key Facts (Critical)",
            "Section 10 does not create a blanket exemption from the general CCoP obligations for OT CII.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "OT-specific controls supplement the broader CII obligations and should be applied in a way that reflects OT operating context rather than used to avoid baseline obligations.",
        ),
        (
            "Reasoning Chain",
            "Check whether the general obligation applies to the CII; confirm that Section 10 supplements rather than replaces the baseline obligations; reject the claim that OT is exempt unless the Code expressly says so.",
        ),
    ]


def b03_025_override() -> list[tuple[str, str]]:
    return [
        ("Clause Refs", "5.15.1, 5.15.2, 5.15.3"),
        (
            "Expected Response",
            "Internal penetration testing can contribute to compliance, but the CCoP text does not support the blanket claim that external testing is always mandatory. The grounded requirements are that penetration testing must be conducted at the cadence required by §5.15.1, additional testing is required after major system changes under §5.15.2, and any third-party penetration testing service providers used must satisfy the accreditation and certification requirements in §5.15.3. The CIIO should therefore ensure that its chosen testing model is competent, properly scoped and consistent with those clauses rather than assume that external testing is categorically required in every case.",
        ),
        (
            "Key Facts (Critical)",
            "The Code mandates penetration-testing cadence and post-major-change testing; it also sets accreditation requirements when third-party testers are used.",
        ),
        (
            "Key Facts (Important/Supporting)",
            "§5.15.3 does not itself make third-party testing universally mandatory; it governs the qualifications required if third-party testers are engaged.",
        ),
        (
            "Reasoning Chain",
            "Separate the mandatory cadence and post-change testing obligations from the third-party accreditation rule; avoid turning the accreditation rule into a blanket external-testing mandate.",
        ),
    ]


def b05_override(test_id: str) -> list[tuple[str, str]] | None:
    mapping = {
        "B05-003": [
            ("Clause Refs", "7.1.1(b) [support: Cybersecurity Act 2018 §14]"),
            (
                "Expected Response",
                "CCoP 2.0 does not itself specify the exact reporting timeframe in the Code. Instead, the CIIO must establish a Cybersecurity Incident Response Plan with an incident-reporting structure that ensures compliance with the Cybersecurity Act and any other applicable laws. Reference: CCoP 2.0 §7.1.1(b); Cybersecurity Act 2018 §14.",
            ),
            ("Key Facts (Critical)", "The IR plan must include an incident-reporting structure that complies with the reporting obligations imposed by the Cybersecurity Act and other applicable laws."),
            ("Key Facts (Important/Supporting)", "The audited CCoP corpus does not itself supply numeric incident-reporting deadlines inside the Code text."),
            ("Reasoning Chain", "Locate the IR-plan requirement in §7.1.1(b); distinguish it from external statutory reporting duties under the Act; do not import unsupported hour-counts into the CCoP answer."),
        ],
        "B05-006": [
            ("Clause Refs", "5.14.1, 5.14.2, 5.14.3, 5.14.4"),
            (
                "Expected Response",
                "CCoP 2.0 does not prescribe quarterly external scans or semi-annual internal scans. Instead, it requires the CIIO to establish vulnerability-identification and tracking processes, remediate vulnerabilities in a timely manner, conduct vulnerability assessments at the required cadence, and perform additional assessment after major system changes. Reference: CCoP 2.0 §5.14.1-§5.14.4.",
            ),
            ("Key Facts (Critical)", "The Code requires a defined vulnerability-assessment process, timely remediation, and vulnerability assessment at the required cadence."),
            ("Key Facts (Important/Supporting)", "Additional assessment is required after major system changes; the corpus does not support the fabricated quarterly and semi-annual scan schedule."),
            ("Reasoning Chain", "Identify the vulnerability-assessment clauses in §5.14; distinguish them from invented scan frequencies; answer in terms of required processes, cadence and post-change assessment."),
        ],
        "B05-009": [
            ("Clause Refs", "5.7.2(c), 5.17.1"),
            (
                "Expected Response",
                "CCoP 2.0 does not provide a single universal rule stating that all data must be encrypted in all circumstances, nor does it prescribe AES-256 specifically. What the audited corpus does show is that remote connections to the CII must use strong encryption and that cryptographic keys used for the CII must be protected against unauthorised access. Reference: CCoP 2.0 §5.7.2(c), §5.17.1.",
            ),
            ("Key Facts (Critical)", "Remote connections to the CII must use strong encryption; cryptographic keys used for the CII must be protected against unauthorised access."),
            ("Key Facts (Important/Supporting)", "The audited corpus does not support a blanket at-rest encryption mandate or a specific AES-256 requirement as a universal rule."),
            ("Reasoning Chain", "Anchor the answer on the specific encryption-related clauses that are actually present in the corpus; avoid broad data-encryption rules that the Code text does not state."),
        ],
        "B05-018": [
            ("Clause Refs", "3.8.1-3.8.4, 5.1.1"),
            (
                "Expected Response",
                "CCoP 2.0 does not contain a specific cross-border data-transfer regime. The Code does not prescribe destination-country adequacy tests, contractual transfer clauses, or CSA notification rules for cross-border transfer as such. If this benchmark is retained, the grounded answer should say that cross-border transfer obligations must be determined under other applicable laws such as the PDPA, while CCoP-related controls remain limited to the CIIO's general CII protections such as access control and outsourcing oversight. Reference: CCoP 2.0 §3.8.1-§3.8.4, §5.1.1.",
            ),
            ("Key Facts (Critical)", "Cross-border transfer is not a standalone CCoP control domain in the audited corpus; other applicable laws govern transfer-specific obligations."),
            ("Key Facts (Important/Supporting)", "Relevant CCoP anchors are limited to general access-control and outsourcing/vendor-management obligations where those controls affect the CII."),
            ("Reasoning Chain", "Distinguish general CII controls from non-CCoP cross-border transfer law; do not fabricate destination-country tests or CSA notification duties that the corpus does not show."),
        ],
        "B05-020": [
            ("Clause Refs", "5.14.1, 5.14.2, 5.14.3, 5.14.4, 5.15.1, 5.15.2"),
            (
                "Expected Response",
                "No. Annual penetration testing alone is not enough to cover vulnerability management under CCoP 2.0. The Code separately requires the CIIO to establish processes to identify and track vulnerabilities, remediate them in a timely manner, and conduct vulnerability assessments at the required cadence; penetration testing is a separate requirement. Reference: CCoP 2.0 §5.14.1-§5.14.4; §5.15.1-§5.15.2.",
            ),
            ("Key Facts (Critical)", "Vulnerability assessment and penetration testing are separate control families in the Code; one does not replace the other."),
            ("Key Facts (Important/Supporting)", "Annual penetration testing may contribute evidence, but the CIIO still needs the broader vulnerability-identification, tracking and remediation process."),
            ("Reasoning Chain", "Separate the vulnerability-assessment requirements in §5.14 from the penetration-testing requirements in §5.15; explain why a yearly pen test does not cover the full vulnerability-management obligation."),
        ],
        "B05-007": [
            ("Clause Refs", "5.15.1, 5.15.2, 5.15.3"),
            (
                "Expected Response",
                "Penetration testing in CCoP 2.0 is governed by §5.15, not §6.2.3. The grounded requirements are: conduct penetration tests at the cadence in §5.15.1, conduct additional penetration tests on relevant CII assets after major system changes under §5.15.2, and ensure that any third-party penetration testing service providers and testers used satisfy the accreditation and certification requirements in §5.15.3. Reference: CCoP 2.0 §5.15.1-§5.15.3.",
            ),
            ("Key Facts (Critical)", "Penetration testing has a defined cadence under §5.15.1 and must also be performed after major system changes under §5.15.2."),
            ("Key Facts (Important/Supporting)", "If third-party testers are used, they must meet the accreditation and certification requirements in §5.15.3; the Code text does not itself say all results must be reported to CSA."),
            ("Reasoning Chain", "Locate the penetration-testing control family in §5.15; separate cadence, post-change testing and third-party qualification requirements; avoid importing unsupported reporting obligations."),
        ],
        "B05-017": [
            ("Clause Refs", "5.10.1(c), 5.10.1(d), 5.10.1(e), 5.10.1(f), 5.10.1(g), 5.10.1(h)"),
            (
                "Expected Response",
                "For OT systems with limited downtime windows, CCoP 2.0 still requires a patch-management process. The grounded answer is that the CIIO must test security patches in a representative environment, prioritise them based on risk, apply them in a timely manner, track patching progress, and use compensating controls where a patch cannot yet be applied. The response can note OT operational constraints, but it should remain anchored on the patch-management process and compensating-control language in §5.10.1 rather than on an unrelated logging clause. Reference: CCoP 2.0 §5.10.1(c)-§5.10.1(h).",
            ),
            ("Key Facts (Critical)", "OT operational constraints do not remove the patch-management obligation; the Code expressly supports testing, risk prioritisation, timely application, tracking and compensating controls."),
            ("Key Facts (Important/Supporting)", "Where immediate patching is not feasible, the CIIO should document the rationale and maintain compensating controls until the patch can be applied."),
            ("Reasoning Chain", "Use the patch-management process in §5.10.1 as the primary anchor; explain how OT downtime constraints are handled through risk prioritisation, testing and compensating controls rather than by ignoring the obligation."),
        ],
        "B05-025": [
            ("Clause Refs", "1.4.3, 1.4.4, 1.5.1, 1.5.2, 1.5.3, 2.1, 1.6"),
            (
                "Expected Response",
                "No. Pre-existing controls are not automatically grandfathered simply because they were implemented before CCoP 2.0. The CIIO must ensure full compliance with the Code by the Compliance Date, subject to the transition-period rule for Existing CII in §1.4.4 and the recurring-requirement timing rules in §1.5. If existing controls do not meet the Code, the resulting gaps must be remediated through the audit-remediation process in §2.1, and a waiver under §1.6 is the proper mechanism if a specific provision cannot be met. Reference: CCoP 2.0 §1.4.3, §1.4.4, §1.5.1-§1.5.3, §2.1, §1.6.",
            ),
            ("Key Facts (Critical)", "The Code does not create a blanket grandfathering rule for older controls; compliance is required by the Compliance Date."),
            ("Key Facts (Important/Supporting)", "Transition-period and recurring-requirement rules affect timing, while remediation and waiver mechanisms address gaps or infeasible requirements."),
            ("Reasoning Chain", "Separate compliance-date and recurring-requirement rules from remediation and waiver mechanisms; avoid treating §2.1 as a grandfathering clause."),
        ],
    }
    return mapping.get(test_id)


def b14_override(test_id: str) -> list[tuple[str, str]] | None:
    mapping = {
        "B14-020": [
            ("Clause Refs", "2.1.2, 5.1.1"),
            (
                "Expected Response",
                "The remediation plan should be anchored on CCoP 2.0 §2.1.2 and should address the weak physical-access condition as an access-control problem affecting the CII. The grounded answer is to document concrete remediation actions, owners, timelines and dependencies for strengthening controls that restrict access to the CII to authorised personnel, activities, processes and devices under §5.1.1. Practical measures may include tightening access authorisation, improving controlled entry into the CII environment, and using compensating controls while permanent improvements are deployed.",
            ),
            ("Key Facts (Critical)", "Audit-finding remediation must be documented and planned under §2.1.2; the substantive control issue is inadequate restriction of access to the CII under §5.1.1."),
            ("Key Facts (Important/Supporting)", "Implementation sequencing can account for cost, disruption and procurement lead time, but the answer should stay anchored on remediation planning rather than inventing a separate facility-security clause."),
            ("Reasoning Chain", "Identify the audit-finding remediation obligation; map the weak physical-access gap to the access-control objective in §5.1.1; propose implementable remediation steps, owners and timelines."),
        ],
        "B14-026": [
            ("Clause Refs", "2.1.2, 2.1.4, 3.2.1"),
            (
                "Expected Response",
                "A zero-budget constraint does not remove the obligation to plan and implement remediation. The grounded answer is that the CIIO must document remediation actions and timelines under §2.1.2, implement them at its own cost under §2.1.4, and prioritise risk treatment under its cybersecurity risk-management framework under §3.2.1. The response may then discuss lower-cost sequencing, existing-tool optimisation and phased remediation as feasibility measures, without inventing a separate CCoP budget exception.",
            ),
            ("Key Facts (Critical)", "The CIIO still has to plan and implement remediation even where budget is constrained."),
            ("Key Facts (Important/Supporting)", "Risk-based prioritisation, phasing and reuse of existing controls are valid feasibility measures, but they do not suspend the remediation obligation."),
            ("Reasoning Chain", "Anchor the answer on the remediation-plan and implementation duties; assess the constraint through the risk-management framework; propose feasible sequencing without implying a budget-based exemption."),
        ],
        "B14-028": [
            ("Clause Refs", "2.1.2 [support: 5.17.1 if encryption is chosen as the remediation design]"),
            (
                "Expected Response",
                "The grounded remediation answer should start with §2.1.2: the CIIO must document a remediation plan for the identified gap, including owners, timeline, dependencies and interim controls. CCoP 2.0 does not contain an explicit clause mandating database encryption as such in the audited corpus. If the CIIO chooses encryption as the remediation measure, key-protection obligations under §5.17.1 become relevant; otherwise the remediation may involve other compensating controls that address the identified risk without pretending the Code contains a standalone database-encryption mandate.",
            ),
            ("Key Facts (Critical)", "The remediation obligation is real, but the audited corpus does not show a direct database-encryption mandate."),
            ("Key Facts (Important/Supporting)", "If encryption is chosen, cryptographic-key protection obligations become relevant; otherwise the plan should stay framed as a risk treatment decision under the remediation process."),
            ("Reasoning Chain", "Anchor on the remediation-plan duty; avoid fabricating a database-encryption clause; explain how encryption can be one remediation option rather than an invented mandatory control."),
        ],
        "B14-007": [
            ("Clause Refs", "2.1.2, 5.1.1"),
            (
                "Expected Response",
                "The grounded remediation answer should keep §2.1.2 as the primary anchor and treat the disabled server-room locks as an access-control weakness affecting the CII. The CIIO should document remediation actions, owners and timelines for restoring effective access restriction to the relevant CII environment, implement interim compensating controls while the underlying issue is fixed, and ensure that access to the CII remains restricted to authorised personnel, activities, processes and devices under §5.1.1. The response should not pretend that the corpus contains a direct server-room-lock clause.",
            ),
            ("Key Facts (Critical)", "Audit-finding remediation must be planned under §2.1.2, and the substantive issue is inadequate restriction of access to the CII under §5.1.1."),
            ("Key Facts (Important/Supporting)", "Compensating controls and operational workarounds may be used while the access-control weakness is being fixed, but the answer should stay grounded in remediation planning and access restriction rather than an invented physical-lock clause."),
            ("Reasoning Chain", "Identify the access-control weakness affecting the CII; anchor the response on the audit-remediation plan; specify concrete remediation and compensating-control steps without inventing a facility-specific clause."),
        ],
    }
    return mapping.get(test_id)


def b18_override() -> list[tuple[str, str]]:
    return [
        ("Clause Refs", "3.8.1, 3.8.2, 3.8.3, 3.8.4, 5.1.3"),
        (
            "Expected Response",
            "The primary CIIO remains responsible and accountable even when functions are outsourced or subcontracted without permission. The CIIO must maintain oversight over outsourced activities, ensure cybersecurity terms are imposed on the external party, validate that the external party complies with those terms, and control vendor access to the CII. Unauthorized subcontracting does not transfer accountability away from the CIIO. Reference: CCoP 2.0 §3.8.1-§3.8.4; §5.1.3.",
        ),
        ("Key Facts (Critical)", "Outsourcing or subcontracting does not transfer accountability away from the primary CIIO; the CIIO must impose and validate cybersecurity obligations on the external party."),
        ("Key Facts (Important/Supporting)", "Vendor or subcontractor access to the CII must remain controlled and overseen by the CIIO."),
        ("Reasoning Chain", "Identify the outsourcing and vendor-management duties; determine that accountability stays with the CIIO; apply the vendor-access control obligations to the unauthorised subcontracting scenario."),
    ]


def b21_013_override() -> list[tuple[str, str]]:
    return [
        ("CCoP Section", "7 (Incident Response) and 10 (OT) for the OT-specific aspect"),
        ("Clause Refs", "7.1.1, 10.4.2"),
        (
            "Expected Response",
            "CCoP 2.0 does not contain a maximum OT incident response time such as 1 hour, 4 hours or 24 hours in the clauses cited here. The incident-response obligation is anchored on §7.1.1, which requires a documented Cybersecurity Incident Response Plan, while §10.4.2 requires alerts, errors and warnings from field controllers to be investigated in a timely manner. A grounded answer is therefore that the CIIO must have defined incident-response procedures and must investigate OT field-controller alerts promptly, but the Code does not prescribe one of the numeric response-time options in the question.",
        ),
        ("Key Facts (Critical)", "§7.1.1 governs the Cybersecurity Incident Response Plan; §10.4.2 requires field-controller alerts, errors and warnings to be investigated in a timely manner."),
        ("Key Facts (Important/Supporting)", "The audited corpus does not contain a numeric OT incident response-time threshold matching the answer choices."),
        ("Reasoning Chain", "Reject the fabricated linkage to threat hunting; locate the real incident-response clause and the field-controller alert clause; answer in terms of plan obligations and timely investigation rather than invented hour thresholds."),
    ]


def b23_override(values: dict[str, str]) -> list[tuple[str, str]]:
    question = values["Question"].lower()
    refs = "1.6.1, 1.6.2, 1.6.3, 3.2.1 [support: Cybersecurity Act 2018 §11(7); external regime-specific requirements remain outside the audited corpus]"
    if any(term in question for term in ["incident reporting", "notification", "reporting to both", "requires notification"]):
        response = (
            "CCoP 2.0 does not set MAS, PDPC or other external reporting timelines in the Code itself. The grounded position is that the CIIO must maintain the incident-reporting structure required by the CCoP for the designated CII and separately comply with each external reporting regime that applies to the scenario. Where timelines differ, the CIIO should design its internal process to meet the applicable obligations in parallel, document the mapping between regimes, and escalate any irreconcilable conflict under its cybersecurity risk-management framework and, where necessary, through the waiver or guidance process. Reference: CCoP 2.0 §1.6, §3.2.1, §7.1.1(b); Cybersecurity Act 2018 §11(7)."
        )
        critical = "CCoP 2.0 does not embed the numeric reporting deadlines of other regimes; the CIIO must satisfy each applicable reporting regime separately."
        supporting = "Conflict handling should be documented through the CIIO's risk-management and escalation process rather than assumed from a generic regulator hierarchy."
        reasoning = "Identify the external regimes that actually apply; confirm that CCoP only requires an incident-reporting structure compliant with the Act and other laws; meet each applicable reporting obligation separately and document conflict escalation."
        clause_refs = "1.6.1, 1.6.2, 1.6.3, 3.2.1, 7.1.1(b) [support: Cybersecurity Act 2018 §11(7)]"
    elif "single audit" in question or "mutually recognized audits" in question or "satisfy both csa and mas" in question:
        response = (
            "CCoP 2.0 does not provide an automatic single-audit or mutual-recognition mechanism across regulators. A CIIO may reuse overlapping evidence where multiple regimes examine similar controls, but compliance with the CCoP and compliance with an external regime remain separate unless that external regime expressly recognises the same audit output. The safe answer is therefore to map common evidence once, then satisfy each regulator's own audit or attestation requirement separately. Reference: CCoP 2.0 §3.2.1; Cybersecurity Act 2018 §15."
        )
        critical = "The audited corpus does not create a universal cross-regulator single-audit rule."
        supporting = "Evidence can be mapped once and reused where appropriate, but regulator-specific acceptance criteria still need to be checked separately."
        reasoning = "Separate evidence reuse from formal regulatory acceptance; determine whether any regime expressly recognises another regime's audit output; otherwise satisfy each audit obligation independently."
        clause_refs = refs
    elif any(term in question for term in ["which prevails", "conflict", "who handles cii compliance"]):
        response = (
            "CCoP 2.0 applies to the designated CII under the Cybersecurity Act, while other sectoral or government requirements continue to apply under their own legal or policy framework. The CCoP corpus does not contain a universal precedence rule that automatically displaces other regulators. The grounded answer is that the CIIO must comply with the applicable CCoP requirements for the designated CII, separately comply with the other governing framework, and manage any conflict through its cybersecurity risk-management process and the waiver or guidance mechanisms where needed. Reference: CCoP 2.0 §1.6, §3.2.1; Cybersecurity Act 2018 §11(7)."
        )
        critical = "The corpus does not support a blanket claim that one regulator simply replaces another for CII compliance."
        supporting = "Conflict resolution should be documented and escalated rather than assumed from informal practice."
        reasoning = "Identify the applicable regimes; apply the CCoP to the designated CII and the other framework on its own terms; use the CIIO's risk-management and escalation process for conflicts."
        clause_refs = refs
    elif "classification" in question:
        response = (
            "CCoP 2.0 does not define government security-classification levels or a formal alignment model with external government classification schemes. A CIIO must comply with the applicable CCoP requirements for the designated CII and separately comply with any government classification rules that apply under their own governing framework. If an external requirement conflicts with a CCoP requirement, the CIIO should assess the issue under its cybersecurity risk-management framework and, where necessary, seek CSA guidance or a waiver under CCoP §1.6 and section 11(7) of the Cybersecurity Act. Reference: CCoP 2.0 §1.6, §3.2.1; Cybersecurity Act 2018 §11(7)."
        )
        critical = "CCoP 2.0 does not itself define government classification tiers or a formal alignment matrix."
        supporting = "Any mapping between government classifications and CCoP controls must be performed under the external government framework, not asserted as a CCoP rule."
        reasoning = "Separate what the CCoP actually prescribes from what the external classification regime prescribes; comply with both where applicable; escalate any true conflict through risk management and waiver channels."
        clause_refs = refs
    else:
        response = (
            "CCoP 2.0 provides the cybersecurity baseline for designated CII only. It does not restate or harmonise the detailed obligations in MAS TRM, PDPA, IM8 or other external regimes inside the CCoP corpus. The grounded answer is therefore to comply with the applicable CCoP requirements for the designated CII, separately comply with the external regime's own requirements, map overlapping evidence where useful, and avoid assuming equivalence or precedence unless the external regime expressly says so. Reference: CCoP 2.0 §1.6, §3.2.1; Cybersecurity Act 2018 §11(7)."
        )
        critical = "External sector or privacy frameworks remain separate obligations; the CCoP corpus does not provide a comprehensive harmonisation table."
        supporting = "Overlap can be managed through evidence mapping, but equivalence or precedence should not be assumed without an express external rule."
        reasoning = "Identify the external regime; confirm the CCoP baseline for the designated CII; map overlapping evidence cautiously; document and escalate any conflict or gap."
        clause_refs = refs
    return [
        ("Clause Refs", clause_refs),
        ("Expected Response", response),
        ("Key Facts (Critical)", critical),
        ("Key Facts (Important/Supporting)", supporting),
        ("Reasoning Chain", reasoning),
    ]


def b24_override(values: dict[str, str]) -> list[tuple[str, str]]:
    question = values["Question"].lower()
    refs = values["Clause Refs"]
    additions = []
    response_parts = [
        "CCoP 2.0 does not define a Code-level serious/substantial classification scheme or prescribe Form A1/A2 labels or fixed hour-count reporting deadlines in the Code itself.",
        "The grounded response is to activate the Cybersecurity Incident Response Plan, follow the incident-reporting structure in the plan so the CIIO complies with the Cybersecurity Act and other applicable laws, contain the affected systems or access path as appropriate, and preserve digital forensic evidence.",
    ]

    if any(term in question for term in ["ransomware", "encrypted", "ransom"]):
        response_parts.append("The CIIO should isolate the affected systems, assess the impact on essential services, and trigger backup, restoration, business continuity or disaster recovery procedures where service delivery is affected.")
        additions.extend(["§8.2.1"])
    if any(term in question for term in ["outage", "disruption", "stop sending data", "database during maintenance", "failover", "substations"]):
        response_parts.append("Where essential service delivery is disrupted or at risk, the CIIO should activate the relevant continuity and recovery procedures and restore operations safely.")
        additions.extend(["§8.2.1"])
    if any(term in question for term in ["exported", "resigning", "former contractor", "credentials", "offboarding"]):
        response_parts.append("Access that is no longer necessary should be disabled or revoked immediately, and the CIIO should investigate what was accessed and whether additional containment is needed.")
        additions.extend(["§5.2.1(e)"])
    if any(term in question for term in ["third-party", "vendor", "fake vendor", "supply chain"]):
        response_parts.append("The CIIO should suspend or tightly control the affected third-party access path and review the applicable outsourcing and vendor-management controls.")
        additions.extend(["§3.8.3", "§3.8.4"])
    if any(term in question for term in ["threat intelligence", "targeting their sector"]):
        response_parts.append("The threat intelligence should be analysed, fed into risk treatment, and used to implement or strengthen mitigating controls before an incident escalates.")
        additions.extend(["§6.4.1", "§6.4.3"])
    if any(term in question for term in ["penetration testing", "critical vulnerability"]):
        response_parts.append("If a critical vulnerability or test result shows real exposure, the CIIO should treat it as an active response and remediation issue, implement compensating controls as needed, and preserve the evidence needed to support remediation and investigation.")
    if any(term in question for term in ["6 months ago", "undetected", "root cause", "unknown if data was exfiltrated"]):
        response_parts.append("After initial containment, the CIIO should perform root-cause analysis and document corrective actions to prevent recurrence.")
        additions.extend(["§7.1.4"])
    elif "incident" in question or "breach" in question or "access" in question:
        response_parts.append("After initial containment, the CIIO should assess impact, determine whether there has been a cybersecurity incident affecting the CII, and perform root-cause analysis where appropriate.")
        additions.extend(["§7.1.4"])

    reference_suffix = ", ".join(dict.fromkeys(additions))
    if reference_suffix:
        response_parts.append(f"Reference: CCoP 2.0 §7.1.1(b), §7.1.1(g), §7.1.1(h){', ' + reference_suffix if reference_suffix else ''}.")
    else:
        response_parts.append("Reference: CCoP 2.0 §7.1.1(b), §7.1.1(g), §7.1.1(h).")

    reasoning = "Confirm the applicable incident-management obligations in the Cybersecurity Incident Response Plan; avoid invented Code-level classifications, forms and hour counts; identify the containment, evidence-preservation, recovery and post-incident actions supported by the actual corpus."
    if "threat intelligence" in question:
        reasoning = "Assess the threat intelligence under §6.4, determine whether it triggers the incident-response process, implement mitigating controls, and preserve alignment between threat-intelligence and incident-management obligations."

    if additions:
        normalized_refs = refs
        plain_refs = normalized_refs.strip()
        extra_text = ", ".join(dict.fromkeys(additions))
        if extra_text and extra_text not in plain_refs:
            normalized_refs = f"{plain_refs}, {extra_text}" if plain_refs else extra_text
    else:
        normalized_refs = refs

    return [
        ("Clause Refs", normalized_refs),
        ("Expected Response", " ".join(response_parts)),
        ("Reasoning Chain", reasoning),
    ]


def missed_override_changes(test_id: str) -> list[tuple[str, str]] | None:
    mapping = {
        "B03-030": [
            (
                "Expected Response",
                "Complying with stricter CAAS requirements may satisfy some overlapping control objectives, but it does not automatically satisfy CCoP 2.0. The CIIO must separately ensure that the designated CII complies with the applicable CCoP requirements and separately comply with CAAS requirements. The grounded answer is to map overlap control by control rather than assume that one regime fully replaces the other.",
            ),
            ("Key Facts (Critical)", "Overlap between regulators does not create automatic equivalence; the designated CII still has to comply with the applicable CCoP requirements."),
            ("Key Facts (Important/Supporting)", "A stricter external regime may reduce duplication for some controls, but the CIIO should confirm coverage rather than assume that one framework fully discharges the other."),
            ("Reasoning Chain", "Identify the two applicable regimes; check for overlap control by control; do not assume that compliance with one regulator automatically satisfies the CCoP."),
        ],
        "B07-007": [
            (
                "Expected Response",
                "Based on the scenario 'No privileged access review', the following compliance gaps are identified:\n\n**Gap Type:** Missing Control\n\n**CCoP Reference:** Section 5.2.2\n\n**Key Gaps:**\n- Periodic access review mandatory for privileged accounts (critical priority)\n- Privilege creep creates excessive exposure (critical priority)\n- 3-year interval exceeds the required periodic review interval (at least once every 12 months) (important priority)\n\n**Recommended Actions:**\n1. Address the control deficiency identified in the gap\n2. Implement compensating measures while the review backlog is cleared\n3. Establish an ongoing periodic review process",
            ),
            ("Key Facts (Important/Supporting)", "3-year interval exceeds the required periodic review interval (at least once every 12 months)."),
        ],
    }
    return mapping.get(test_id)


def approved_override_changes(defect_id: str, row: ET.Element) -> list[tuple[str, str]] | None:
    values = get_row_values(row)
    test_id = values["Test ID"]
    if defect_id in {"B24-016-D3", "B24-017-D3", "B24-018-D3", "B24-021-D3"}:
        return b24_override(values)
    if defect_id == "B01-013-D1":
        return b01_013_override()
    if defect_id == "B01-015-D1":
        return b01_015_override()
    if defect_id == "B02-013-D1":
        return b02_013_override()
    if defect_id == "B02-015-D1":
        return b02_015_override()
    if test_id.startswith("B04-"):
        return [("Expected Response", rewrite_b04_expected_response(values["Expected Response"]))]
    if test_id.startswith("B12-"):
        return [
            ("Expected Response", rewrite_b12_expected_response(values)),
            ("Reasoning Chain", rewrite_b12_reasoning(values)),
        ]
    if test_id.startswith("B13-"):
        if test_id == "B13-016":
            return b13_016_override()
        if test_id == "B13-019":
            return b13_019_override()
        return [("Expected Response", rewrite_b13_generic(values))]
    return None


def bad_fix_override_changes(defect_id: str, row: ET.Element) -> list[tuple[str, str]] | None:
    values = get_row_values(row)
    test_id = values["Test ID"]
    direct = {
        "B01-001-D1": b01_001_override(),
        "B01-006-D1": b01_006_override(),
        "B01-021-D1": b01_021_override(),
        "B02-018-D1": b02_018_override(),
        "B03-025-D1": b03_025_override(),
    }
    if defect_id in direct:
        return direct[defect_id]
    if test_id.startswith("B05-"):
        return b05_override(test_id)
    if test_id.startswith("B14-"):
        return b14_override(test_id)
    if defect_id == "B18-023-D1":
        return b18_override()
    if defect_id == "B21-013-D1":
        return b21_013_override()
    if defect_id == "B12-011-D1":
        return [
            ("CCoP Section", "5"),
            ("Clause Refs", "5.14.1, 5.14.2, 5.14.3, 5.14.4, 5.10.1 [support: Auditing Guidelines for CII]"),
            ("Expected Response", "**Audit Perspective: Vulnerability management program**\n\n**CSA Auditor Viewpoint:**\nWhen assessing vulnerability management under CCoP 2.0 §5.14 and related patch-management controls, a CSA auditor would examine:\n- Whether the CIIO has established vulnerability-identification, tracking and assessment processes\n- Whether vulnerabilities are prioritised and remediated in a timely manner\n- Whether additional assessment is performed after major system changes\n- Whether patch-management actions are tracked and exceptions are documented\n\n**Risk Manager Audit Preparation:**\nTo prepare for audit of vulnerability management:\n- Auditor reviews vulnerability assessment outputs, vulnerability tracking, remediation records and patch-management evidence\n- Evidence: vulnerability assessment reports, remediation tracking, patch testing and deployment records, exception approvals\n- Risk Manager: ensure that vulnerability and patch records show timely risk-based treatment and documented follow-up\n\nReference: CCoP 2.0 §5.14.1-§5.14.4; §5.10.1; CSA Guidelines for Auditing CII."),
            ("Key Facts (Critical)", "Auditor checks that vulnerability identification, tracking and remediation processes exist and operate effectively; evidence should show timely risk-based treatment of findings."),
            ("Key Facts (Important/Supporting)", "Patch-management records, exception handling and post-major-change assessment evidence should align with the broader vulnerability-management process."),
            ("Reasoning Chain", "Identify control: Vulnerability management; Determine CCoP clause(s): 5.14.1, 5.14.2, 5.14.3, 5.14.4, 5.10.1; Consider auditor expectations for evidence and verification; Identify Risk Manager preparation activities."),
        ]
    if defect_id == "B12-012-D1":
        return [
            ("CCoP Section", "3 and 5"),
            ("Clause Refs", "3.3.1, 5.7.2(c), 5.17.1 [support: Auditing Guidelines for CII]"),
            ("Expected Response", "**Audit Perspective: Data protection practices**\n\n**CSA Auditor Viewpoint:**\nCCoP 2.0 does not prescribe a standalone data-classification scheme in the audited corpus. A grounded audit answer is therefore to examine how the CIIO's own policies define the handling of CII-sensitive data and whether the controls that the Code expressly requires are implemented and evidenced.\n\n**Risk Manager Audit Preparation:**\nTo prepare for audit of data protection practices:\n- Auditor reviews the CIIO's internal data-handling or protection policies relevant to the CII\n- Evidence: approved policies and procedures, evidence that remote connections use strong encryption where required, and evidence that cryptographic keys are protected against unauthorised access\n- Risk Manager: be prepared to explain how internal data-handling rules map to the CII protections required by the Code\n\nReference: CCoP 2.0 §3.3.1, §5.7.2(c), §5.17.1; CSA Guidelines for Auditing CII."),
            ("Key Facts (Critical)", "The audited corpus does not contain a standalone data-classification mandate; the answer should instead anchor on CIIO-defined policies and the specific protection clauses actually present in the Code."),
            ("Key Facts (Important/Supporting)", "Evidence should show how the CIIO's own data-handling rules map to required CII protections such as strong encryption for remote connections and key protection."),
            ("Reasoning Chain", "Identify control: Data protection practices; determine the CCoP clauses that actually speak to data-protection controls; avoid pretending the Code contains a resolved data-classification clause family."),
        ]
    if defect_id == "B12-017-D1":
        return [
            ("CCoP Section", "Support: Cybersecurity Act 2018 §15 / Auditing Guidelines"),
            ("Clause Refs", "Cybersecurity Act 2018 §15 [support: Auditing Guidelines for CII §6.2-§6.4; Form A1/A2 are submission templates, not CCoP clauses]"),
            ("Expected Response", "**Audit Perspective: Audit submission documentation**\n\n**CSA Auditor Viewpoint:**\nForm A1 and Form A2 are submission templates, not CCoP clauses. A grounded audit-preparation answer should focus on the statutory audit obligation and the evidence package needed to support the cybersecurity audit.\n\n**Risk Manager Audit Preparation:**\nTo prepare for audit submission:\n- Auditor reviews whether the evidence package covers the designated CII, the audit period and the applicable compliance criteria\n- Evidence: completed submission templates where required, supporting control evidence, audit working papers, and records that tie the submission back to the designated CII and audit scope\n- Risk Manager: ensure the submission artefacts are complete and that each submission item is supported by traceable evidence\n\nReference: Cybersecurity Act 2018 §15; CSA's Guidelines for Auditing CII §6.2-§6.4."),
            ("Key Facts (Critical)", "Form A1/A2 are submission artefacts rather than CCoP clauses; the grounded anchors are the statutory audit obligation and the audit-guideline scope and criteria."),
            ("Reasoning Chain", "Identify the actual legal and audit-guideline basis for the submission; treat Form A1/A2 as templates rather than clauses; prepare traceable supporting evidence for the audit package."),
        ]
    if defect_id == "B12-019-D1":
        return [
            ("CCoP Section", "2"),
            ("Clause Refs", "2.1.1, 2.1.2, 2.1.4 [support: Cybersecurity Act 2018 §16; Auditing Guidelines for CII]"),
            ("Expected Response", "**Audit Perspective: Past enforcement actions or directives**\n\n**CSA Auditor Viewpoint:**\nA grounded audit answer should focus on whether past findings, directives or remediation obligations were tracked, planned and completed. The relevant CCoP anchors are the audit-remediation clauses, with statutory directions supported by the Cybersecurity Act.\n\n**Risk Manager Audit Preparation:**\nTo prepare for audit of past enforcement actions or directives:\n- Auditor reviews prior audit findings, remediation plans, completion status updates and correspondence relating to statutory directions or follow-up requirements\n- Evidence: prior audit reports, remediation plans submitted to the Commissioner, completion evidence, status updates and CSA correspondence\n- Risk Manager: ensure that all past remediation actions and relevant directions can be traced to documented closure evidence\n\nReference: CCoP 2.0 §2.1.1, §2.1.2, §2.1.4; Cybersecurity Act 2018 §16; CSA Guidelines for Auditing CII."),
            ("Key Facts (Critical)", "The grounded CCoP hooks are the audit-remediation obligations, not a generic 'enforcement' clause."),
            ("Reasoning Chain", "Map the topic to remediation planning, implementation and closure evidence; use the statutory direction power as support rather than treating 'enforcement' as a CCoP clause."),
        ]
    if defect_id.endswith("-D2") and test_id.startswith("B23-"):
        return b23_override(values)
    if test_id.startswith("B24-") and defect_id.endswith(("-D2", "-D4")):
        return b24_override(values)
    return None


def main():
    if not BACKUP_PATH.exists():
        shutil.copy2(WORKBOOK_PATH, BACKUP_PATH)

    sheet_root, all_files = load_sheet_xml()
    row_map = build_row_map(sheet_root)
    audit, decision_map = load_data()

    per_row_notes = defaultdict(lambda: {"applied": [], "verifier_rewrite": [], "pending_rewrite": [], "false_positive": [], "approved_manual": [], "missed_applied": [], "missed": []})
    applied_count = 0
    transformed_count = 0
    manual_approved_count = 0
    verifier_rewrite_count = 0

    approved_defects = [d for d in audit if decision_map[d["defect_id"]]["decision"] == "APPROVED"]
    approved_defects.sort(key=lambda item: natural_key(item["defect_id"]))

    for defect in approved_defects:
        row = row_map.get(defect["test_id"])
        if row is None:
            continue
        defect_id = defect["defect_id"]
        fix = defect.get("proposed_fix") or {}
        applied_any = False
        direct_or_transform = []
        used_override = False

        changes = []
        if fix.get("field_to_change") and "new_value" in fix:
            changes.append((fix["field_to_change"], fix["new_value"]))
        for extra in fix.get("additional_changes") or []:
            if extra.get("field_to_change") and "new_value" in extra:
                changes.append((extra["field_to_change"], extra["new_value"]))

        for field, value in changes:
            ok, mode = apply_change_to_field(row, field, value)
            if ok:
                applied_any = True
                direct_or_transform.append(mode)
            else:
                overrides = approved_override_changes(defect_id, row)
                if overrides and apply_override_changes(row, overrides):
                    applied_any = True
                    used_override = True
                    break
                per_row_notes[defect["test_id"]]["approved_manual"].append(defect_id)
                manual_approved_count += 1
                applied_any = False
                break

        if applied_any:
            per_row_notes[defect["test_id"]]["applied"].append(defect_id)
            applied_count += 1
            if used_override:
                transformed_count += 1
            else:
                transformed_count += sum(1 for mode in direct_or_transform if mode == "transformed")

    for defect in audit:
        decision = decision_map[defect["defect_id"]]["decision"]
        notes = per_row_notes[defect["test_id"]]
        if decision == "REJECTED_BAD_FIX":
            row = row_map.get(defect["test_id"])
            overrides = bad_fix_override_changes(defect["defect_id"], row) if row is not None else None
            if row is not None and overrides and apply_override_changes(row, overrides):
                notes["verifier_rewrite"].append(defect["defect_id"])
                verifier_rewrite_count += 1
            else:
                notes["pending_rewrite"].append(defect["defect_id"])
        elif decision == "REJECTED_FALSE_POSITIVE":
            notes["false_positive"].append(defect["defect_id"])

    extra_decisions = json.loads(DECISIONS_PATH.read_text())
    for entry in extra_decisions:
        if "-M" in entry["defect_id"]:
            row = row_map.get(entry["test_id"])
            overrides = missed_override_changes(entry["test_id"]) if row is not None else None
            if row is not None and overrides and apply_override_changes(row, overrides):
                per_row_notes[entry["test_id"]]["missed_applied"].append(entry["defect_id"])
            else:
                per_row_notes[entry["test_id"]]["missed"].append(entry["defect_id"])

    for test_id, notes in per_row_notes.items():
        row = row_map.get(test_id)
        if row is None:
            continue
        remarks = []
        if notes["applied"]:
            remarks.append("Applied: " + ", ".join(sorted(set(notes["applied"]), key=natural_key)))
        if notes["verifier_rewrite"]:
            remarks.append("Verifier rewrite applied: " + ", ".join(sorted(set(notes["verifier_rewrite"]), key=natural_key)))
        if notes["approved_manual"]:
            remarks.append("Approved-manual-review: " + ", ".join(sorted(set(notes["approved_manual"]), key=natural_key)))
        if notes["pending_rewrite"]:
            remarks.append("Pending rewrite: " + ", ".join(sorted(set(notes["pending_rewrite"]), key=natural_key)))
        if notes["false_positive"]:
            remarks.append("Do not apply: " + ", ".join(sorted(set(notes["false_positive"]), key=natural_key)))
        if notes["missed_applied"]:
            remarks.append("Missed-by-auditor fix applied: " + ", ".join(sorted(set(notes["missed_applied"]), key=natural_key)))
        if notes["missed"]:
            remarks.append("Missed by auditor: " + ", ".join(sorted(set(notes["missed"]), key=natural_key)))

        if not remarks:
            continue

        remarks_text = "Verifier 2026-04-30 | " + " | ".join(remarks)
        remarks_cell = get_or_create_cell(row, FIELD_TO_COL["Remarks"])
        set_inline_text(remarks_cell, remarks_text)

    # Ensure dimension still spans Remarks column.
    dimension = sheet_root.find("a:dimension", NS)
    if dimension is not None:
        dimension.attrib["ref"] = "A1:S436"

    xml_bytes = ET.tostring(sheet_root, encoding="utf-8", xml_declaration=True)

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp_path = Path(tmp.name)

    with ZipFile(tmp_path, "w", compression=ZIP_DEFLATED) as out_zip:
        for name, data in all_files:
            if name == "xl/worksheets/sheet1.xml":
                out_zip.writestr(name, xml_bytes)
            else:
                out_zip.writestr(name, data)

    shutil.move(tmp_path, WORKBOOK_PATH)

    print(f"approved defects processed: {len(approved_defects)}")
    print(f"approved defects applied: {applied_count}")
    print(f"approved field transforms: {transformed_count}")
    print(f"approved defects requiring manual review: {manual_approved_count}")
    print(f"verifier rewrites applied: {verifier_rewrite_count}")
    print(f"backup: {BACKUP_PATH}")


if __name__ == "__main__":
    main()
