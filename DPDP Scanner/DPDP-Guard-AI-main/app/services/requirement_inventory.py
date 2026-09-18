"""
Deterministic DPDP compliance requirement inventory.

The inventory is the scanner's checklist.
Gemini must evaluate these requirements; it must NOT decide
which legal requirements exist.

Based on:
- Digital Personal Data Protection Act, 2023
- Digital Personal Data Protection Rules, 2025
"""

REQUIREMENT_INVENTORY = [

    # ============================================================
    # DPDP ACT 2023 — GENERAL DATA FIDUCIARY OBLIGATIONS
    # ============================================================

    {
        "id": "ACT_SEC_4",
        "title": "Lawful Processing of Personal Data",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 4",
        "actor": "data_fiduciary",
        "requirement": (
            "Personal data must be processed only in accordance with "
            "the Act and for a lawful purpose, based on consent or a "
            "legitimate use."
        ),
        "evidence_fields": [
            "privacy_policy",
            "personal_data_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_5",
        "title": "Notice Before or With Consent Request",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 5(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "Every request for consent must be accompanied or preceded "
            "by a notice informing the Data Principal of the personal "
            "data proposed to be processed, the purpose of processing, "
            "how rights may be exercised, and how a complaint may be "
            "made to the Board."
        ),
        "evidence_fields": [
            "privacy_policy",
            "personal_data_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_5_2",
        "title": "Notice for Pre-Act Consent",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 5(2)",
        "actor": "data_fiduciary",
        "requirement": (
            "Where consent was obtained before commencement of the Act, "
            "the Data Fiduciary must provide the required notice as soon "
            "as reasonably practicable."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_5_3",
        "title": "Notice Language Accessibility",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 5(3)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Principal must be given an option to access the "
            "notice in English or a language specified in the Eighth "
            "Schedule to the Constitution."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_6_1",
        "title": "Valid Consent",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 6(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "Consent must be free, specific, informed, unconditional "
            "and unambiguous, involve clear affirmative action, relate "
            "to the specified purpose, and be limited to personal data "
            "necessary for that purpose."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_6_2",
        "title": "Invalid Consent Provisions",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 6(2)",
        "actor": "data_fiduciary",
        "requirement": (
            "Any part of consent that infringes the Act, the Rules or "
            "another applicable law is invalid to the extent of that "
            "infringement."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_6_3",
        "title": "Clear and Plain Consent Request",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 6(3)",
        "actor": "data_fiduciary",
        "requirement": (
            "A request for consent must be presented in clear and plain "
            "language and provide the required language-access option "
            "and applicable contact details for exercising rights."
        ),
        "evidence_fields": [
            "consent_information",
            "privacy_policy",
            "contact_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_6_4",
        "title": "Withdrawal of Consent",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 6(4)",
        "actor": "data_fiduciary",
        "requirement": (
            "A Data Principal must be able to withdraw consent at any "
            "time with ease comparable to giving consent."
        ),
        "evidence_fields": [
            "consent_information",
            "privacy_policy",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_6_6",
        "title": "Cessation of Processing After Withdrawal",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 6(6)",
        "actor": "data_fiduciary",
        "requirement": (
            "After withdrawal of consent, the Data Fiduciary must within "
            "a reasonable time cease and cause its Data Processors to "
            "cease processing the Data Principal's personal data unless "
            "continued processing is otherwise required or authorised."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
            "retention_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_6_10",
        "title": "Proof of Notice and Consent",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 6(10)",
        "actor": "data_fiduciary",
        "requirement": (
            "Where consent is the basis of processing and the issue "
            "arises in a proceeding, the Data Fiduciary must be able "
            "to prove that notice was given and consent was obtained "
            "in accordance with the Act and Rules."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
        ],
        "conditional": True,
    },

    # ============================================================
    # SECTION 8 — GENERAL DATA FIDUCIARY OBLIGATIONS
    # ============================================================

    {
        "id": "ACT_SEC_8_1",
        "title": "Overall Data Fiduciary Responsibility",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary remains responsible for compliance "
            "with the Act and Rules for processing undertaken by it "
            "or on its behalf by a Data Processor."
        ),
        "evidence_fields": [
            "privacy_policy",
            "terms_of_use",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_8_2",
        "title": "Data Processor Contract",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(2)",
        "actor": "data_fiduciary",
        "requirement": (
            "A Data Processor used for activities related to offering "
            "goods or services must be engaged under a valid contract."
        ),
        "evidence_fields": [
            "privacy_policy",
            "terms_of_use",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_8_3",
        "title": "Accuracy and Consistency of Personal Data",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(3)",
        "actor": "data_fiduciary",
        "requirement": (
            "Where personal data is likely to be used for a decision "
            "affecting the Data Principal or disclosed to another Data "
            "Fiduciary, the Data Fiduciary must ensure completeness, "
            "accuracy and consistency."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_8_4",
        "title": "Technical and Organisational Measures",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(4)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must implement appropriate technical "
            "and organisational measures to ensure effective observance "
            "of the Act and Rules."
        ),
        "evidence_fields": [
            "security_policy",
            "privacy_policy",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_8_5",
        "title": "Reasonable Security Safeguards",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(5)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must protect personal data in its "
            "possession or control by taking reasonable security "
            "safeguards to prevent personal data breaches."
        ),
        "evidence_fields": [
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_8_6",
        "title": "Personal Data Breach Intimation",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(6)",
        "actor": "data_fiduciary",
        "requirement": (
            "In the event of a personal data breach, the Data Fiduciary "
            "must intimate the Board and each affected Data Principal "
            "in the prescribed form and manner."
        ),
        "evidence_fields": [
            "breach_information",
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_8_7",
        "title": "Erasure After Withdrawal or Purpose Completion",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(7)",
        "actor": "data_fiduciary",
        "requirement": (
            "Unless retention is necessary under applicable law, the "
            "Data Fiduciary must erase personal data after withdrawal "
            "of consent or when the specified purpose is no longer "
            "being served, whichever is earlier, and cause its Data "
            "Processor to erase the data made available to it."
        ),
        "evidence_fields": [
            "retention_information",
            "privacy_policy",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_8_9",
        "title": "Processing Contact Information",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(9)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must publish business contact information "
            "of a Data Protection Officer, if applicable, or a person "
            "able to answer questions raised by Data Principals about "
            "processing of their personal data."
        ),
        "evidence_fields": [
            "contact_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_8_10",
        "title": "Grievance Redressal Mechanism",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 8(10)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must establish an effective mechanism "
            "to redress grievances of Data Principals."
        ),
        "evidence_fields": [
            "grievance_information",
            "contact_information",
        ],
        "conditional": False,
    },

    # ============================================================
    # SECTION 9 — CHILDREN
    # ============================================================

    {
        "id": "ACT_SEC_9_1",
        "title": "Verifiable Parental Consent",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 9(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "Before processing personal data of a child or a person "
            "with disability who has a lawful guardian, the Data "
            "Fiduciary must obtain verifiable consent of the parent "
            "or lawful guardian as applicable."
        ),
        "evidence_fields": [
            "consent_information",
            "personal_data_information",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_9_2",
        "title": "Protection of Children's Well-Being",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 9(2)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must not undertake processing of "
            "children's personal data likely to cause detrimental "
            "effect on the well-being of a child."
        ),
        "evidence_fields": [
            "privacy_policy",
            "personal_data_information",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_9_3",
        "title": "Restrictions on Children's Tracking and Advertising",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 9(3)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must not undertake tracking or "
            "behavioural monitoring of children or targeted advertising "
            "directed at children."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
            "personal_data_information",
        ],
        "conditional": True,
    },

    # ============================================================
    # SECTION 10 — SIGNIFICANT DATA FIDUCIARY
    # ============================================================

    {
        "id": "ACT_SEC_10_DPO",
        "title": "Significant Data Fiduciary DPO",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 10(2)(a)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must appoint a Data Protection "
            "Officer who is based in India, is responsible to the Board "
            "or similar governing body, represents the Significant Data "
            "Fiduciary and is the point of contact for grievance redressal."
        ),
        "evidence_fields": [
            "contact_information",
            "grievance_information",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_10_AUDITOR",
        "title": "Independent Data Auditor",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 10(2)(b)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must appoint an independent "
            "data auditor to carry out a data audit."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_10_DPIA",
        "title": "Periodic Data Protection Impact Assessment",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 10(2)(c)(i)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must undertake periodic "
            "Data Protection Impact Assessments."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    {
        "id": "ACT_SEC_10_AUDIT",
        "title": "Periodic Compliance Audit",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 10(2)(c)(ii)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must undertake periodic audits."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    # ============================================================
    # DATA PRINCIPAL RIGHTS THAT REQUIRE DATA FIDUCIARY SUPPORT
    # ============================================================

    {
        "id": "ACT_SEC_11",
        "title": "Access to Personal Data Information",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 11",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must enable the Data Principal to "
            "obtain the prescribed information concerning personal "
            "data being processed and relevant sharing."
        ),
        "evidence_fields": [
            "privacy_policy",
            "contact_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_12",
        "title": "Correction, Completion, Updating and Erasure",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 12",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must provide the Data Principal with "
            "means to exercise applicable rights to correction, "
            "completion, updating and erasure, and must act on requests "
            "as prescribed by the Act."
        ),
        "evidence_fields": [
            "privacy_policy",
            "contact_information",
            "retention_information",
        ],
        "conditional": False,
    },

    {
        "id": "ACT_SEC_13",
        "title": "Data Principal Grievance Rights",
        "source": "dpdp_act_2023.pdf",
        "legal_reference": "Section 13",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must provide readily available means "
            "for Data Principals to raise grievances and respond to "
            "such grievances within the prescribed period."
        ),
        "evidence_fields": [
            "grievance_information",
            "contact_information",
        ],
        "conditional": False,
    },

    # ============================================================
    # DPDP RULES 2025
    # ============================================================

    {
        "id": "RULE_3",
        "title": "Standalone Notice",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 3(a)",
        "actor": "data_fiduciary",
        "requirement": (
            "The notice must be presented and understandable independently "
            "of other information made available by the Data Fiduciary."
        ),
        "evidence_fields": [
            "privacy_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_3_ITEMISED_DATA",
        "title": "Itemised Personal Data in Notice",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 3(b)(i)",
        "actor": "data_fiduciary",
        "requirement": (
            "The notice must provide an itemised description of the "
            "personal data being processed."
        ),
        "evidence_fields": [
            "personal_data_information",
            "privacy_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_3_PURPOSE",
        "title": "Specified Purpose in Notice",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 3(b)(ii)",
        "actor": "data_fiduciary",
        "requirement": (
            "The notice must specify the purpose or purposes of "
            "processing and provide a specific description of the "
            "goods, services or uses enabled by the processing."
        ),
        "evidence_fields": [
            "privacy_policy",
            "personal_data_information",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_3_LINKS",
        "title": "Notice Rights and Complaint Links",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 3(c)",
        "actor": "data_fiduciary",
        "requirement": (
            "The notice must provide the relevant communication link "
            "and describe means through which the Data Principal may "
            "withdraw consent, exercise rights and make a complaint "
            "to the Board."
        ),
        "evidence_fields": [
            "privacy_policy",
            "consent_information",
            "grievance_information",
        ],
        "conditional": False,
    },

    # ------------------------------------------------------------
    # RULE 6 — SECURITY
    # ------------------------------------------------------------

    {
        "id": "RULE_6_ENCRYPTION",
        "title": "Security Measures for Personal Data",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(a)",
        "actor": "data_fiduciary",
        "requirement": (
            "Appropriate data security measures must protect personal "
            "data, including encryption, obfuscation, masking or "
            "virtual tokens as appropriate."
        ),
        "evidence_fields": [
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_6_ACCESS",
        "title": "Access Control",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(b)",
        "actor": "data_fiduciary",
        "requirement": (
            "Appropriate measures must control access to computer "
            "resources used by the Data Fiduciary or applicable "
            "Data Processor."
        ),
        "evidence_fields": [
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_6_LOGGING",
        "title": "Access Logging and Monitoring",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(c)",
        "actor": "data_fiduciary",
        "requirement": (
            "Appropriate logs, monitoring and review must provide "
            "visibility into access to personal data for detecting, "
            "investigating and remediating unauthorised access."
        ),
        "evidence_fields": [
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_6_BACKUPS",
        "title": "Business Continuity and Backups",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(d)",
        "actor": "data_fiduciary",
        "requirement": (
            "Reasonable measures must support continued processing "
            "when confidentiality, integrity or availability of "
            "personal data is compromised, including appropriate "
            "data backups."
        ),
        "evidence_fields": [
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_6_LOG_RETENTION",
        "title": "Security Log Retention",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(e)",
        "actor": "data_fiduciary",
        "requirement": (
            "Relevant logs and personal data must be retained for "
            "one year for detection, investigation, remediation and "
            "continued processing, unless applicable law requires otherwise."
        ),
        "evidence_fields": [
            "security_policy",
            "retention_information",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_6_PROCESSOR_CONTRACT",
        "title": "Security Safeguards in Processor Contracts",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(f)",
        "actor": "data_fiduciary",
        "requirement": (
            "Where applicable, the contract between the Data Fiduciary "
            "and Data Processor must contain appropriate provisions "
            "for reasonable security safeguards."
        ),
        "evidence_fields": [
            "security_policy",
            "privacy_policy",
        ],
        "conditional": True,
    },

    {
        "id": "RULE_6_TECH_ORG",
        "title": "Technical and Organisational Security Measures",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 6(1)(g)",
        "actor": "data_fiduciary",
        "requirement": (
            "Appropriate technical and organisational measures must "
            "ensure effective observance of security safeguards."
        ),
        "evidence_fields": [
            "security_policy",
        ],
        "conditional": False,
    },

    # ------------------------------------------------------------
    # RULE 7 — BREACH
    # ------------------------------------------------------------

    {
        "id": "RULE_7_PRINCIPAL_BREACH",
        "title": "Breach Notification to Affected Data Principals",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 7(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "Affected Data Principals must be informed without delay "
            "in concise, clear and plain language about the breach, "
            "its consequences, mitigation measures, safety measures "
            "and relevant business contact information."
        ),
        "evidence_fields": [
            "breach_information",
            "security_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_7_BOARD_BREACH",
        "title": "Breach Notification to the Board",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 7(2)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must notify the Board without delay "
            "and provide the prescribed detailed information within "
            "seventy-two hours or such longer period as permitted "
            "by the Board."
        ),
        "evidence_fields": [
            "breach_information",
            "security_policy",
        ],
        "conditional": False,
    },

    # ------------------------------------------------------------
    # RULE 8 — ERASURE AND RETENTION
    # ------------------------------------------------------------

    {
        "id": "RULE_8_ERASURE",
        "title": "Specified-Purpose Erasure",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 8(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "For applicable classes and purposes in the Third Schedule, "
            "personal data must be erased after the specified period "
            "when the Data Principal neither approaches the Data "
            "Fiduciary nor exercises rights, unless retention is "
            "required by law."
        ),
        "evidence_fields": [
            "retention_information",
            "privacy_policy",
        ],
        "conditional": True,
    },

    {
        "id": "RULE_8_48_HOURS",
        "title": "Pre-Erasure Notice",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 8(2)",
        "actor": "data_fiduciary",
        "requirement": (
            "At least forty-eight hours before the applicable erasure "
            "period expires, the Data Fiduciary must inform the Data "
            "Principal that the personal data will be erased unless "
            "the Data Principal logs in, initiates contact or exercises "
            "rights."
        ),
        "evidence_fields": [
            "retention_information",
            "privacy_policy",
        ],
        "conditional": True,
    },

    {
        "id": "RULE_8_ONE_YEAR",
        "title": "One-Year Processing Data and Log Retention",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 8(3)",
        "actor": "data_fiduciary",
        "requirement": (
            "For processing specified in the Seventh Schedule, the "
            "Data Fiduciary must retain relevant personal data, "
            "associated traffic data and processing logs for at least "
            "one year before erasure, unless another law or Government "
            "notification requires otherwise."
        ),
        "evidence_fields": [
            "retention_information",
            "security_policy",
        ],
        "conditional": True,
    },

    # ------------------------------------------------------------
    # RULE 9 — CONTACT
    # ------------------------------------------------------------

    {
        "id": "RULE_9_CONTACT",
        "title": "Processing Questions Contact Information",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 9",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must prominently publish on its website "
            "or app the business contact information of the DPO, if "
            "applicable, or a person able to answer Data Principal "
            "questions about processing of personal data."
        ),
        "evidence_fields": [
            "contact_information",
        ],
        "conditional": False,
    },

    # ------------------------------------------------------------
    # RULE 10 — CHILDREN
    # ------------------------------------------------------------

    {
        "id": "RULE_10_CHILD_CONSENT",
        "title": "Verifiable Parental Consent Mechanism",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 10",
        "actor": "data_fiduciary",
        "requirement": (
            "Before processing a child's personal data, the Data "
            "Fiduciary must adopt appropriate technical and "
            "organisational measures to obtain verifiable parental "
            "consent and verify that the person identifying themselves "
            "as the parent is an identifiable adult."
        ),
        "evidence_fields": [
            "consent_information",
            "privacy_policy",
        ],
        "conditional": True,
    },

    # ------------------------------------------------------------
    # RULE 11 — PERSON WITH DISABILITY
    # ------------------------------------------------------------

    {
        "id": "RULE_11_GUARDIAN",
        "title": "Verification of Lawful Guardian",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 11",
        "actor": "data_fiduciary",
        "requirement": (
            "When obtaining verifiable consent from a person claiming "
            "to be the lawful guardian of a person with disability, "
            "the Data Fiduciary must exercise due diligence to verify "
            "that the guardian was appointed by the applicable lawful "
            "authority."
        ),
        "evidence_fields": [
            "consent_information",
            "privacy_policy",
        ],
        "conditional": True,
    },

    # ------------------------------------------------------------
    # RULE 13 — SIGNIFICANT DATA FIDUCIARY
    # ------------------------------------------------------------

    {
        "id": "RULE_13_DPIA",
        "title": "Annual SDF DPIA and Audit",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 13(1)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must undertake a Data "
            "Protection Impact Assessment and an audit once every "
            "twelve months."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    {
        "id": "RULE_13_BOARD_REPORT",
        "title": "SDF DPIA and Audit Reporting",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 13(2)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must cause the person "
            "conducting the DPIA and audit to furnish a report "
            "containing significant observations to the Board."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    {
        "id": "RULE_13_ALGORITHMIC_RISK",
        "title": "SDF Algorithmic Risk Due Diligence",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 13(3)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must exercise due diligence "
            "to verify that technical measures, including algorithmic "
            "software used for processing personal data, are not likely "
            "to pose a risk to Data Principal rights."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    {
        "id": "RULE_13_LOCALISATION",
        "title": "SDF Government-Specified Data Localisation",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 13(4)",
        "actor": "significant_data_fiduciary",
        "requirement": (
            "A Significant Data Fiduciary must comply with applicable "
            "Government restrictions preventing specified personal "
            "data and related traffic data from being transferred "
            "outside India."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },

    # ------------------------------------------------------------
    # RULE 14 — DATA PRINCIPAL RIGHTS
    # ------------------------------------------------------------

    {
        "id": "RULE_14_RIGHTS_MEANS",
        "title": "Published Means to Exercise Rights",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 14(1)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must prominently publish the means "
            "through which a Data Principal can request exercise "
            "of rights and any identifier required to identify the "
            "Data Principal."
        ),
        "evidence_fields": [
            "contact_information",
            "privacy_policy",
        ],
        "conditional": False,
    },

    {
        "id": "RULE_14_GRIEVANCE_90_DAYS",
        "title": "Grievance Response Period",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 14(3)",
        "actor": "data_fiduciary",
        "requirement": (
            "The Data Fiduciary must publish its grievance redressal "
            "system and implement appropriate technical and "
            "organisational measures to respond to grievances within "
            "a reasonable period not exceeding ninety days."
        ),
        "evidence_fields": [
            "grievance_information",
            "contact_information",
        ],
        "conditional": False,
    },

    # ------------------------------------------------------------
    # RULE 15 — CROSS-BORDER TRANSFER
    # ------------------------------------------------------------

    {
        "id": "RULE_15_CROSS_BORDER",
        "title": "Cross-Border Transfer Requirements",
        "source": "dpdp_rules_2025.pdf",
        "legal_reference": "Rule 15",
        "actor": "data_fiduciary",
        "requirement": (
            "Where applicable Government requirements restrict making "
            "personal data available to a foreign State or an entity "
            "under its control, the Data Fiduciary must comply with "
            "those requirements."
        ),
        "evidence_fields": [
            "privacy_policy",
            "page_text",
        ],
        "conditional": True,
    },
]


def get_all_requirements() -> list[dict]:
    """
    Return a copy of the complete requirement inventory.
    """
    return REQUIREMENT_INVENTORY.copy()


def get_requirement(requirement_id: str) -> dict | None:
    """
    Return a single requirement by ID.
    """
    for requirement in REQUIREMENT_INVENTORY:
        if requirement["id"] == requirement_id:
            return requirement

    return None