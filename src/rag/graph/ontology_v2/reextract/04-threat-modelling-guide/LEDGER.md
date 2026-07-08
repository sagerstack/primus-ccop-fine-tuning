# Re-extraction ledger — Threat Modelling Guide

Source PDF: `supplementary/Guide-to-Cyber-Threat-Modelling.pdf`  |  chunker: `section_based`

## Counts (verified this run)
- segmented chunks: **16**
- clean (no noise flag): **11**  (68%)
- flagged: **5**

## Noise breakdown
- `tiny`: 3
- `table`: 2

## Shared-blob groups: 0 (covering 0 chunks)

## Flagged samples

### `Threat Modelling Guide::1`  ['tiny']  (14 chars)
```
1 INTRODUCTION
```

### `Threat Modelling Guide::2`  ['tiny']  (10 chars)
```
2 APPROACH
```

### `Threat Modelling Guide::3`  ['tiny']  (13 chars)
```
3 METHODOLOGY
```

### `Threat Modelling Guide::3.5`  ['table']  (5945 chars)
```
3.5 Step 4: Attack Modelling

After identifying threat events relevant to the system, Users should link these events into a possible sequence of attack. Attack modelling describes an attacker's intrusion approach so that  Users  can  identify  mitigation  controls  needed  to  defend  the  system  a
```

### `Threat Modelling Guide::4`  ['table']  (16825 chars)
```
4 REFERENCES

Bodeau  D.J.,  McCollum,  C.  D.  Homeland  Security  Systems  Engineering  &amp;  Development Institute. (2018). Cyber Threat Modeling: Survey, Assessment and Representative Framework

Cybersecurity Agency  of Singapore. (2019).  Guide to Conducting  Cybersecurity Risk Assessment for
```

## First 8 clean clauses (spot-check verbatim vs PDF)

### `Threat Modelling Guide::1.1`  (1224 chars)
```
1.1 Importance of Threat Modelling

Due to finite resources of the system owner, it is difficult to mitigate every vulnerability within a system. Therefore, system owners must prioritise risks and treat them accordingly. A key step in determining risk is identifying threat events, which contribute t
```

### `Threat Modelling Guide::1.2`  (1418 chars)
```
1.2 Purpose of Document

CSA issued  the Guide  to  Conducting  Cybersecurity  Risk  Assessment  for  Critical  Information Infrastructure in December 2019 (subsequently revised in Feb 2021). The document provided guidance  to  Critical  Information  Infrastructure  Owners  (CIIOs)  on  performing
```

### `Threat Modelling Guide::1.3`  (1194 chars)
```
1.3 Scope

This document is for individuals or groups who would like to build a threat model for their system(s). They can use the results of the threat model as inputs to other assessments, such as cybersecurity risk  assessments, to prioritise risk controls.  Individuals  and  groups  using this g
```

### `Threat Modelling Guide::2.1`  (1948 chars)
```
2.1 System Level Approach

Figure 1 : Hierarchy of threat analysis

<!-- image -->

Users can approach threat analysis at three different tiers -from a management perspective, from a system perspective, and from an equipment or application perspective. Below is a general description of each tier. Th
```

### `Threat Modelling Guide::2.2`  (1752 chars)
```
2.2 Common Missteps in Threat Modelling

While system owners seek to model threat events for their systems, some pitfalls hinder their process or diminish the effectiveness of their threat model. Some of the common problems include:

- Misdirected or unbalanced threat focus -in some cases where scop
```

### `Threat Modelling Guide::2.3`  (1500 chars)
```
2.3 Integrating Threat Modelling into Risk Assessment Process

As mentioned in Section 1.2 above, CSA issued the Guide to Conducting Cybersecurity Risk Assessment for Critical Information Infrastructure ,  which provides guidance on performing a proper cybersecurity risk assessment. This document su
```

### `Threat Modelling Guide::3.1`  (718 chars)
```
3.1 Overview of Method

The threat modelling method proposed in this guide comprises broadly the following 4 steps:

- Step  1 -Scope  Definition,  which  involves  gathering  information  and  demarcating perimeter boundary;
- Step  2 -System  Decomposition,  which  involves  identifying  system  c
```

### `Threat Modelling Guide::3.2`  (1819 chars)
```
3.2 Step 1: Preliminaries and Scope Definition

Users  should  establish  the  technical  scope,  system  architecture,  and  system  components before  performing  threat  modelling  for  a  system.  Users  should  also  examine  the  security perimeters, interfaces, and data flows to characterise
```