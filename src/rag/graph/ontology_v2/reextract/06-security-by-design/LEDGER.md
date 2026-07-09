# Re-extraction ledger — Security By Design

Source PDF: `supplementary/Security_By_Design_Framework.pdf`  |  chunker: `clause_aware`

## Counts (verified this run)
- segmented chunks: **138**
- clean (no noise flag): **74**  (53%)
- flagged: **64**

## Noise breakdown
- `table`: 59
- `tiny`: 5
- `toc-dot-leader`: 1

## Shared-blob groups: 0 (covering 0 chunks)

## Flagged samples

### `Security By Design::preamble`  ['toc-dot-leader', 'table']  (14114 chars)
```
<!-- image -->

## Security-by-Design Framework Version: 1.0

## Document History

|   Version No. | Date             | Author                             | Changes   |
|---------------|------------------|------------------------------------|-----------|
|             1 | 09 November 2017 | Cyber Se
```

### `Security By Design::5.3`  ['tiny']  (32 chars)
```
5.3 Security-by-Design Lifecycle
```

### `Security By Design::5.4`  ['tiny']  (31 chars)
```
5.4 Security-by-Design Approach
```

### `Security By Design::5.6`  ['tiny']  (22 chars)
```
5.6 Security Processes
```

### `Security By Design::5.7`  ['tiny']  (14 chars)
```
5.7 Activities
```

### `Security By Design::5.8`  ['tiny']  (17 chars)
```
5.8 Control Gates
```

### `Security By Design::6.1`  ['table']  (752 chars)
```
6.1 Phase: INITIATION

At  the  Initiation  phase,  early  integration  of  security  considerations  is  key  to  the success of the implementing a secured system. Threats, security requirements and potential constraints of functionality and integration are considered at this phase. Security is loo
```

### `Security By Design::6.1::table::0`  ['table']  (369 chars)
```
| Security Process                    | Activities                      |
|-------------------------------------|---------------------------------|
| Security Planning & Risk Assessment | Security Planning               |
| Security Planning & Risk Assessment | Systems Security Classification |
| Se
```

### `Security By Design::6.1.1.1`  ['table']  (6263 chars)
```
6.1.1.1 Activity: Security Planning

| Description:                   | Security planning is to be conducted as part of the initiation and planning phase. It includes:  Identifying and confirming key security roles in the system development project  Ensuring all key stakeholders have a commonunder
```

### `Security By Design::6.1.1.1::table::0`  ['table']  (2021 chars)
```
| Description:                   | Security planning is to be conducted as part of the initiation and planning phase. It includes:  Identifying and confirming key security roles in the system development project  Ensuring all key stakeholders have a commonunderstanding of the goals, implications,
```

### `Security By Design::6.1.1.1::table::1`  ['table']  (4203 chars)
```
|                      | include whether the security assessment is performed in-house or outsourced. The Project Manager is also responsible to outline key security milestones and activities with inputs from the Security Officer / Consultant. Developer The Developer is consulted as part of security
```

### `Security By Design::6.1.1.2`  ['table']  (4279 chars)
```
6.1.1.2 Activity:  System Security Classification

| Description:   | In order to perform threat and risk assessment, it is important to first determine the security classification of the system. The security classification will be used in conjunction with the threats and vulnerability information i
```

## First 8 clean clauses (spot-check verbatim vs PDF)

### `Security By Design::1.1`  (299 chars)
```
1.1 Most organisations adopt a Systems Development Lifecycle (SDLC) methodology for the development and implementation of computer systems. SDLC is a multi-step lifecycle process to deliver computer systems to ensure good-quality systems that meet specifications and, within time and cost estimates.
```

### `Security By Design::1.2`  (452 chars)
```
1.2 While most organisations acknowledge that security is an important consideration in developing computer systems, costs and business performance often take precedence over security. Even though awareness has been elevated on security issues, most organisations focus on applying security only at t
```

### `Security By Design::1.3`  (289 chars)
```
1.3 An  effective  way  to  protect  computer  systems  against  cyber  threats  is  to  integrate security  into  every  step  of  the  SDLC,  from  initiation,  to  development,  to  deployment  and eventual disposal of the system. This approach is the Security-by-Design (SBD) approach.
```

### `Security By Design::1.4`  (1055 chars)
```
1.4 Security-by-Design is an approach to software and hardware development that seeks to minimise  systems  vulnerabilities  and  reduce  the  attack  surface  through  designing  and building security in every phase of the SDLC. This includes incorporating security specifications in the design, con
```

### `Security By Design::1.5`  (318 chars)
```
1.5 Specific to cybersecurity, Security-by-Design addresses the cyber protection considerations throughout a system's lifecycle. This includes security design specifically for the identification, protection, detection, response and recovery capabilities to strengthen the cyber resiliency of the syst
```

### `Security By Design::2.1`  (941 chars)
```
2.1 This document establishes a framework to guide organisations in building security into their  SDLC,  through  the  alignment  of  security-related  processes/activities  alongside  SDLC processes. This would result in more cost-effective and risk-appropriate security considerations and controls
```

### `Security By Design::2.1(a)`  (129 chars)
```
(a) Establish a  Security-by-Design framework that stakeholders can take reference where Security-by-Design approach is mandated.
```

### `Security By Design::2.1(b)`  (157 chars)
```
(b) Establish SBD processes to ensure that security risks are managed from the start, and continuously assessed during the SDLC through a lifecycle approach.
```