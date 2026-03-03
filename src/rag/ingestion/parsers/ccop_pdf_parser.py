"""
CCoP Document Registry

Defines the CCoP 2.0 document corpus with per-document parsing and chunking strategies.
"""

import logging
from dataclasses import dataclass

from rag.ingestion.models import ChunkerType, ParserType

logger = logging.getLogger(__name__)


@dataclass
class CcopDocument:
    """Configuration for a CCoP document."""

    name: str
    path: str
    parser_type: ParserType
    chunker_type: ChunkerType


# Document configuration - all 8 CCoP documents with per-document strategy
CCOP_DOCUMENTS = [
    CcopDocument(
        name="CCoP 2.0",
        path="CCoP---Second-Edition_Revision-One.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.CLAUSE_AWARE,
    ),
    CcopDocument(
        name="CCoP Response to Feedback",
        path="RESPONSE-TO-FEEDBACK.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.SECTION_BASED,
    ),
    CcopDocument(
        name="Auditing Guidelines",
        path="supplementary/Guidelines_for_Auditing_Critical_Information_Infrastructure.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.SECTION_BASED,
    ),
    CcopDocument(
        name="Threat Modelling Guide",
        path="supplementary/Guide-to-Cyber-Threat-Modelling.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.SECTION_BASED,
    ),
    CcopDocument(
        name="Risk Assessment Guide",
        path="supplementary/Guide-to-Conducting-Cybersecurity-Risk-Assessment-for-CII.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.SECTION_BASED,
    ),
    CcopDocument(
        name="Security By Design",
        path="supplementary/Security_By_Design_Framework.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.CLAUSE_AWARE,
    ),
    CcopDocument(
        name="Ensign CCoP Guide",
        path="references/Ensign's_Cybersecurity_Guide_on_CCoP_2_0_for_CII_Sep_2022.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.SECTION_BASED,
    ),
    CcopDocument(
        name="Cybersecurity Act 2018",
        path="references/Cybersecurity Act 2018.pdf",
        parser_type=ParserType.CLASSIC,
        chunker_type=ChunkerType.SECTION_BASED,
    ),
]
