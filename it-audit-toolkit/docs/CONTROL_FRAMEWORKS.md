# IT Control Frameworks Reference

This document provides reference information for the major IT governance and security frameworks that inform the controls in the IT Audit Toolkit.

---

## Table of Contents

1. [Framework Overview](#framework-overview)
2. [COBIT 2019](#cobit-2019)
3. [ISO 27001:2022](#iso-270012022)
4. [NIST Cybersecurity Framework (CSF) 2.0](#nist-cybersecurity-framework-csf-20)
5. [PCI-DSS v4.0](#pci-dss-v40)
6. [SOX Section 404 (IT General Controls)](#sox-section-404-it-general-controls)
7. [ITIL 4](#itil-4)
8. [Framework Mapping Matrix](#framework-mapping-matrix)

---

## Framework Overview

The IT Audit Toolkit maps controls to multiple frameworks to support organizations subject to various regulatory and governance requirements. Understanding how these frameworks relate helps auditors provide cross-framework coverage with a single set of tests.

| Framework | Focus | Governing Body | Current Version |
|-----------|-------|----------------|-----------------|
| COBIT | IT governance and management | ISACA | 2019 |
| ISO 27001 | Information security management | ISO/IEC | 2022 |
| NIST CSF | Cybersecurity risk management | NIST (US) | 2.0 |
| PCI-DSS | Payment card data security | PCI SSC | 4.0 |
| SOX | Financial reporting controls | SEC/PCAOB (US) | Ongoing |
| ITIL | IT service management | Axelos/PeopleCert | 4 |

---

## COBIT 2019

### Overview

COBIT (Control Objectives for Information and Related Technologies) is a comprehensive framework for IT governance and management developed by ISACA. COBIT 2019 provides a set of governance and management objectives organized into five domains.

### Governance and Management Objectives

#### Governance Domain: Evaluate, Direct, and Monitor (EDM)
- **EDM01**: Ensured Governance Framework Setting and Maintenance
- **EDM02**: Ensured Benefits Delivery
- **EDM03**: Ensured Risk Optimization
- **EDM04**: Ensured Resource Optimization
- **EDM05**: Ensured Stakeholder Engagement

#### Management Domain: Align, Plan, and Organize (APO)
- **APO01**: Managed I&T Management Framework
- **APO02**: Managed Strategy
- **APO03**: Managed Enterprise Architecture
- **APO04**: Managed Innovation
- **APO05**: Managed Portfolio
- **APO06**: Managed Budget and Costs
- **APO07**: Managed Human Resources
- **APO08**: Managed Relationships
- **APO09**: Managed Service Agreements
- **APO10**: Managed Vendors
- **APO11**: Managed Quality
- **APO12**: Managed Risk
- **APO13**: Managed Security
- **APO14**: Managed Data

#### Management Domain: Build, Acquire, and Implement (BAI)
- **BAI01**: Managed Programs
- **BAI02**: Managed Requirements Definition
- **BAI03**: Managed Solutions Identification and Build
- **BAI04**: Managed Availability and Capacity
- **BAI05**: Managed Organizational Change
- **BAI06**: Managed IT Changes (key for change management auditing)
- **BAI07**: Managed IT Change Acceptance and Transitioning
- **BAI08**: Managed Knowledge
- **BAI09**: Managed Assets
- **BAI10**: Managed Configuration
- **BAI11**: Managed Projects

#### Management Domain: Deliver, Service, and Support (DSS)
- **DSS01**: Managed Operations
- **DSS02**: Managed Service Requests and Incidents
- **DSS03**: Managed Problems
- **DSS04**: Managed Continuity (key for backup/DR auditing)
- **DSS05**: Managed Security Services (key for access/network auditing)
- **DSS06**: Managed Business Process Controls

#### Management Domain: Monitor, Evaluate, and Assess (MEA)
- **MEA01**: Managed Performance and Conformance Monitoring
- **MEA02**: Managed System of Internal Control
- **MEA03**: Managed Compliance with External Requirements
- **MEA04**: Managed Assurance

### Key COBIT Objectives for IT Auditing

| Toolkit Domain | Primary COBIT Objectives |
|---------------|-------------------------|
| Access Control | DSS05.04, DSS05.05 |
| Change Management | BAI06.01, BAI06.02, BAI06.03 |
| Incident Response | DSS02.01-DSS02.07 |
| Data Backup | DSS04.01, DSS04.04, DSS04.07 |
| Network Security | DSS05.02, DSS05.03, DSS05.07 |
| Compliance | MEA03.01, MEA03.02, MEA03.03 |

---

## ISO 27001:2022

### Overview

ISO/IEC 27001:2022 is the international standard for Information Security Management Systems (ISMS). It specifies requirements for establishing, implementing, maintaining, and continually improving an ISMS. Annex A provides a reference set of 93 information security controls organized into four themes.

### Annex A Control Themes

#### Organizational Controls (A.5) - 37 Controls
Key controls for IT auditing:
- **A.5.3**: Segregation of Duties
- **A.5.15**: Access Control
- **A.5.16**: Identity Management
- **A.5.17**: Authentication Information
- **A.5.18**: Access Rights
- **A.5.19-A.5.22**: Supplier Relationships
- **A.5.24-A.5.28**: Incident Management
- **A.5.30**: ICT Readiness for Business Continuity
- **A.5.31-A.5.36**: Compliance

#### People Controls (A.6) - 8 Controls
- **A.6.1**: Screening
- **A.6.2**: Terms and Conditions of Employment
- **A.6.3**: Information Security Awareness, Education and Training
- **A.6.7**: Remote Working

#### Physical Controls (A.7) - 14 Controls
- **A.7.1**: Physical Security Perimeters
- **A.7.2**: Physical Entry
- **A.7.3**: Securing Offices, Rooms and Facilities
- **A.7.4**: Physical Security Monitoring

#### Technological Controls (A.8) - 34 Controls
Key controls for IT auditing:
- **A.8.2**: Privileged Access Rights
- **A.8.5**: Secure Authentication
- **A.8.8**: Management of Technical Vulnerabilities
- **A.8.9**: Configuration Management
- **A.8.13**: Information Backup
- **A.8.15**: Logging
- **A.8.16**: Monitoring Activities
- **A.8.20**: Networks Security
- **A.8.22**: Segregation of Networks
- **A.8.24**: Use of Cryptography
- **A.8.29**: Security Testing in Development and Acceptance
- **A.8.31**: Separation of Development, Test, and Production Environments
- **A.8.32**: Change Management

---

## NIST Cybersecurity Framework (CSF) 2.0

### Overview

The NIST Cybersecurity Framework provides a structured approach to managing cybersecurity risk. CSF 2.0 (released February 2024) organizes cybersecurity activities into six core functions.

### Core Functions

#### GOVERN (GV) - New in CSF 2.0
Establishes and monitors the organization's cybersecurity risk management strategy, expectations, and policy:
- GV.OC: Organizational Context
- GV.RM: Risk Management Strategy
- GV.RR: Roles, Responsibilities, and Authorities
- GV.PO: Policy
- GV.OV: Oversight
- GV.SC: Cybersecurity Supply Chain Risk Management

#### IDENTIFY (ID)
Understanding the organization's assets, risks, and capabilities:
- ID.AM: Asset Management
- ID.RA: Risk Assessment
- ID.IM: Improvement

#### PROTECT (PR)
Safeguards to manage cybersecurity risk:
- **PR.AA**: Identity Management, Authentication, and Access Control
- **PR.AT**: Awareness and Training
- **PR.DS**: Data Security
- **PR.PS**: Platform Security
- **PR.IR**: Technology Infrastructure Resilience

#### DETECT (DE)
Timely discovery of cybersecurity events:
- **DE.CM**: Continuous Monitoring
- **DE.AE**: Adverse Event Analysis

#### RESPOND (RS)
Actions regarding a detected cybersecurity incident:
- **RS.MA**: Incident Management
- **RS.AN**: Incident Analysis
- **RS.CO**: Incident Response Reporting and Communication
- **RS.MI**: Incident Mitigation

#### RECOVER (RC)
Restoring capabilities impaired by a cybersecurity incident:
- **RC.RP**: Incident Recovery Plan Execution
- **RC.CO**: Incident Recovery Communication

---

## PCI-DSS v4.0

### Overview

The Payment Card Industry Data Security Standard (PCI-DSS) is a set of security requirements designed to protect cardholder data. Version 4.0 was released in March 2022 with a mandatory compliance date of March 31, 2025 for most requirements.

### Requirements

#### Build and Maintain a Secure Network and Systems
- **Requirement 1**: Install and Maintain Network Security Controls
- **Requirement 2**: Apply Secure Configurations to All System Components

#### Protect Account Data
- **Requirement 3**: Protect Stored Account Data
- **Requirement 4**: Protect Cardholder Data with Strong Cryptography During Transmission

#### Maintain a Vulnerability Management Program
- **Requirement 5**: Protect All Systems and Networks from Malicious Software
- **Requirement 6**: Develop and Maintain Secure Systems and Software

#### Implement Strong Access Control Measures
- **Requirement 7**: Restrict Access to System Components and Cardholder Data by Business Need to Know
- **Requirement 8**: Identify Users and Authenticate Access to System Components
- **Requirement 9**: Restrict Physical Access to Cardholder Data

#### Regularly Monitor and Test Networks
- **Requirement 10**: Log and Monitor All Access to System Components and Cardholder Data
- **Requirement 11**: Test Security of Systems and Networks Regularly

#### Maintain an Information Security Policy
- **Requirement 12**: Support Information Security with Organizational Policies and Programs

### Key Changes in v4.0
- Customized approach as alternative to defined approach
- Enhanced authentication requirements (MFA for all CDE access)
- Targeted risk analysis for certain requirements
- Roles and responsibilities explicitly defined for each requirement
- Web application firewall requirement for public-facing applications

---

## SOX Section 404 (IT General Controls)

### Overview

Section 404 of the Sarbanes-Oxley Act requires management to assess and report on the effectiveness of internal controls over financial reporting (ICFR). IT General Controls (ITGCs) are a critical component of ICFR for organizations that use IT systems for financial processing and reporting.

### ITGC Control Categories

#### 1. Access to Programs and Data
- User account provisioning and de-provisioning
- Authentication controls (password policies, MFA)
- Authorization and role-based access
- Periodic access reviews
- Privileged access management
- Physical access to IT assets

#### 2. Program Changes
- Change request and approval process
- Testing before production deployment
- Segregation of duties (developers vs. deployers)
- Emergency change procedures
- Post-implementation review
- Version control and release management

#### 3. Program Development
- System development lifecycle (SDLC) methodology
- Requirements documentation and approval
- Security considerations in design
- User acceptance testing
- Data migration controls
- Go-live authorization

#### 4. Computer Operations
- Job scheduling and monitoring
- Backup and recovery procedures
- Incident management
- Problem management
- Capacity management
- Service level management

### SOX Testing Approach
- ITGCs are tested in the context of financially significant applications
- Testing covers the full fiscal year (not a point in time)
- Deficiencies are classified as: control deficiency, significant deficiency, or material weakness
- Material weaknesses must be disclosed in the annual report

---

## ITIL 4

### Overview

ITIL (Information Technology Infrastructure Library) 4 is the most widely adopted framework for IT service management. While not a compliance framework, ITIL practices directly support IT audit control objectives.

### Relevant ITIL 4 Practices

| ITIL Practice | Audit Domain | Relevance |
|--------------|-------------|-----------|
| Change Enablement | Change Management | Primary framework for change processes |
| Incident Management | Incident Response | Incident detection, classification, resolution |
| Service Configuration Management | Change Management | CMDB and configuration baseline management |
| Information Security Management | All Domains | Overarching security governance |
| Service Continuity Management | Data Backup | Business continuity and disaster recovery |
| Release Management | Change Management | Deployment and release controls |
| Problem Management | Incident Response | Root cause analysis and prevention |

---

## Framework Mapping Matrix

The following matrix shows how the toolkit's audit domains map across frameworks:

| Toolkit Control | ISO 27001:2022 | COBIT 2019 | NIST CSF 2.0 | PCI-DSS v4.0 | SOX ITGC |
|----------------|---------------|-----------|-------------|-------------|---------|
| User Provisioning | A.5.16 | DSS05.04 | PR.AA | 7.2 | Access |
| De-provisioning | A.5.18 | DSS05.04 | PR.AA | 8.1.3 | Access |
| Password Policy | A.5.17 | DSS05.04 | PR.AA | 8.3.6 | Access |
| MFA | A.5.17 | DSS05.04 | PR.AA | 8.4 | Access |
| Privileged Access | A.8.2 | DSS05.04 | PR.AA | 7.2.2 | Access |
| Access Reviews | A.5.18 | DSS05.04 | PR.AA | 7.2.3 | Access |
| Change Process | A.8.32 | BAI06.01 | PR.PS | N/A | Changes |
| Change Approval | A.8.32 | BAI06.01 | PR.PS | N/A | Changes |
| Change Testing | A.8.29 | BAI06.02 | PR.PS | 6.3 | Changes |
| Env Segregation | A.8.31 | BAI03.05 | PR.PS | N/A | Changes |
| Incident Plan | A.5.24 | DSS02.01 | RS.MA | 12.10.1 | Operations |
| Incident Detection | A.8.16 | DSS05.07 | DE.CM | 10.4 | Operations |
| Backup Policy | A.8.13 | DSS04.01 | PR.IR | 9.5 | Operations |
| DR Testing | A.5.30 | DSS04.04 | RC.RP | 12.10.2 | Operations |
| Firewall Mgmt | A.8.20 | DSS05.02 | PR.PS | 1.2 | Access |
| Network Segment | A.8.22 | DSS05.02 | PR.PS | 1.3 | Access |
| Vuln Scanning | A.8.8 | DSS05.01 | DE.CM | 11.3 | Operations |
| Encryption | A.8.24 | DSS05.02 | PR.DS | 4.2 | Access |
