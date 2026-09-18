// Comprehensive DPDP Act (2023) and DPDP Rules (2025) Metadata & Helper Utilities

export const DPDP_ACT_METADATA = {
  // DPDP ACT 2023
  ACT_SEC_4: {
    law: "DPDP Act 2023",
    ref: "Section 4",
    title: "Lawful Processing of Personal Data",
    explanation:
      "Organizations may only process personal data for lawful purposes with user consent or for legitimate statutory uses authorized by law.",
    defaultGuidance:
      "State explicit lawful purposes for data collection across all intake forms and public policies.",
  },
  ACT_SEC_5: {
    law: "DPDP Act 2023",
    ref: "Section 5(1)",
    title: "Notice Accompanying Consent Request",
    explanation:
      "A clear privacy notice must accompany every consent request, detailing the personal data collected, processing purpose, rights, and complaint channels.",
    defaultGuidance:
      "Ensure privacy notices are accessible immediately prior to or alongside all data submission forms.",
  },
  ACT_SEC_5_2: {
    law: "DPDP Act 2023",
    ref: "Section 5(2)",
    title: "Notice for Pre-Act Consent",
    explanation:
      "For personal data collected before the Act commenced, organizations must provide a retrospective notice informing users of continued processing.",
    defaultGuidance:
      "Deploy retrospective notice communications to legacy registered users.",
  },
  ACT_SEC_5_3: {
    law: "DPDP Act 2023",
    ref: "Section 5(3)",
    title: "Multilingual Notice Accessibility",
    explanation:
      "Privacy notices and consent requests must be made available in English and any of the 22 languages specified in the Eighth Schedule to the Constitution.",
    defaultGuidance:
      "Provide accessible language options (such as Hindi, Tamil, Telugu, etc.) alongside English notices.",
  },
  ACT_SEC_6_1: {
    law: "DPDP Act 2023",
    ref: "Section 6(1)",
    title: "Valid and Informed Consent",
    explanation:
      "Consent must be freely given, specific, informed, unconditional, unambiguous, and signified through a clear affirmative action.",
    defaultGuidance:
      "Use unticked opt-in checkboxes and explicit confirmation buttons on registration and service forms.",
  },
  ACT_SEC_6_2: {
    law: "DPDP Act 2023",
    ref: "Section 6(2)",
    title: "Invalid Consent Conditions",
    explanation:
      "Consent provisions that waive statutory rights or violate the Act are legally invalid to the extent of the inconsistency.",
    defaultGuidance:
      "Review privacy clauses to eliminate forced waivers of statutory data protection rights.",
  },
  ACT_SEC_6_3: {
    law: "DPDP Act 2023",
    ref: "Section 6(3)",
    title: "Clear, Plain & Standalone Consent",
    explanation:
      "Consent requests must be clear, written in plain language, and presented independently without being buried inside long general terms.",
    defaultGuidance:
      "Separate privacy consent prompts from general service terms and contractual agreements.",
  },
  ACT_SEC_6_4: {
    law: "DPDP Act 2023",
    ref: "Section 6(4)",
    title: "Right to Withdraw Consent",
    explanation:
      "Users have the right to withdraw consent at any time, and the withdrawal mechanism must be as easy to use as giving consent.",
    defaultGuidance:
      "Provide a 1-click or direct settings option to withdraw consent or delete profile data.",
  },
  ACT_SEC_6_6: {
    law: "DPDP Act 2023",
    ref: "Section 6(6)",
    title: "Cessation of Processing Upon Withdrawal",
    explanation:
      "When a user withdraws consent, the organization and its processors must immediately cease processing and erase the user's data unless required by law.",
    defaultGuidance:
      "Implement automated workflows to stop active processing and schedule prompt data deletion upon withdrawal.",
  },
  ACT_SEC_6_10: {
    law: "DPDP Act 2023",
    ref: "Section 6(10)",
    title: "Proof of Notice and Consent",
    explanation:
      "In any dispute, the burden of proving that notice was provided and valid consent was obtained rests on the organization.",
    defaultGuidance:
      "Maintain cryptographically verifiable or auditable timestamped consent logs with IP, user ID, and policy version.",
  },
  ACT_SEC_8_1: {
    law: "DPDP Act 2023",
    ref: "Section 8(1)",
    title: "Data Fiduciary Accountability",
    explanation:
      "The organization remains responsible for compliance with the Act for all processing, even when processing is carried out by external contractors.",
    defaultGuidance:
      "Document organizational accountability and assign responsible officers for data protection compliance.",
  },
  ACT_SEC_8_2: {
    law: "DPDP Act 2023",
    ref: "Section 8(2)",
    title: "Data Processor Contract Requirement",
    explanation:
      "Organizations may only engage data processors under a valid, legally binding contract addressing security and statutory obligations.",
    defaultGuidance:
      "Execute DPDP-compliant Data Processing Agreements (DPAs) with all cloud providers, vendors, and partners.",
  },
  ACT_SEC_8_3: {
    law: "DPDP Act 2023",
    ref: "Section 8(3)",
    title: "Accuracy and Completeness of Data",
    explanation:
      "Organizations must ensure personal data is reasonably accurate, complete, and consistent when used to make decisions affecting the user.",
    defaultGuidance:
      "Provide users with accessible self-service profile editors to correct and update personal details.",
  },
  ACT_SEC_8_4: {
    law: "DPDP Act 2023",
    ref: "Section 8(4)",
    title: "Technical & Organisational Measures",
    explanation:
      "Organizations must implement appropriate technical tools and organizational governance structures to secure compliance with the Act.",
    defaultGuidance:
      "Formalize committee oversight, administrative roles, and system maintenance controls.",
  },
  ACT_SEC_8_5: {
    law: "DPDP Act 2023",
    ref: "Section 8(5)",
    title: "Reasonable Security Safeguards",
    explanation:
      "Organizations must implement reasonable security safeguards (firewalls, encryption, access controls) to prevent personal data breaches.",
    defaultGuidance:
      "Maintain active endpoint security, traffic inspection firewalls, and network access restrictions.",
  },
  ACT_SEC_8_6: {
    law: "DPDP Act 2023",
    ref: "Section 8(6)",
    title: "Data Breach Intimation",
    explanation:
      "In the event of a personal data breach, the organization must promptly notify affected users and intimate the Data Protection Board.",
    defaultGuidance:
      "Establish an incident response protocol specifying direct email/SMS notifications upon security events.",
  },
  ACT_SEC_8_7: {
    law: "DPDP Act 2023",
    ref: "Section 8(7)",
    title: "Data Erasure Upon Purpose Completion",
    explanation:
      "Personal data must be erased as soon as the specified purpose for which it was collected is completed, unless retention is mandated by law.",
    defaultGuidance:
      "Define explicit data retention schedules (e.g. 30 days for video logs, academic cycle for students) and automatic purge jobs.",
  },
  ACT_SEC_8_9: {
    law: "DPDP Act 2023",
    ref: "Section 8(9)",
    title: "Published Processing Contact",
    explanation:
      "Organizations must prominently publish contact details of a Data Protection Officer or authorized officer who can answer privacy queries.",
    defaultGuidance:
      "Publish an explicit email address and phone number for privacy and data inquiries in website footers.",
  },
  ACT_SEC_8_10: {
    law: "DPDP Act 2023",
    ref: "Section 8(10)",
    title: "Published Grievance Mechanism",
    explanation:
      "The organization must establish and publish a readily accessible grievance redressal mechanism for data principals.",
    defaultGuidance:
      "Host an online grievance registration portal with designated nodal officers and committee contacts.",
  },
  ACT_SEC_9_1: {
    law: "DPDP Act 2023",
    ref: "Section 9(1)",
    title: "Verifiable Parental Consent",
    explanation:
      "Before processing any personal data of a child (under 18) or a person with a disability, organizations must obtain verifiable parental consent.",
    defaultGuidance:
      "Include a parent/guardian verification mechanism for services accessible to minors.",
  },
  ACT_SEC_9_2: {
    law: "DPDP Act 2023",
    ref: "Section 9(2)",
    title: "Child Well-Being Protection",
    explanation:
      "Organizations are prohibited from undertaking any personal data processing that is likely to cause a detrimental effect on the well-being of a child.",
    defaultGuidance:
      "Maintain active anti-ragging, anti-harassment, and student safety policies prohibiting discriminatory data use.",
  },
  ACT_SEC_9_3: {
    law: "DPDP Act 2023",
    ref: "Section 9(3)",
    title: "Ban on Child Tracking & Targeted Ads",
    explanation:
      "Organizations must not track, monitor the behavior of, or direct targeted advertising toward children.",
    defaultGuidance:
      "Prohibit behavioral trackers, advertising pixels, and commercial exploitation across student accounts.",
  },
  ACT_SEC_10_DPO: {
    law: "DPDP Act 2023",
    ref: "Section 10(2)(a)",
    title: "SDF: India-Based DPO Appointment",
    explanation:
      "Significant Data Fiduciaries must appoint an India-based Data Protection Officer responsible directly to the Board of Directors.",
    defaultGuidance:
      "Appoint and publish the credentials of an India-resident DPO if designated as an SDF.",
  },
  ACT_SEC_10_AUDITOR: {
    law: "DPDP Act 2023",
    ref: "Section 10(2)(b)",
    title: "SDF: Independent Data Auditor",
    explanation:
      "Significant Data Fiduciaries must appoint an independent data auditor to evaluate compliance with the Act.",
    defaultGuidance:
      "Engage an accredited external firm for periodic independent data protection audits.",
  },
  ACT_SEC_10_DPIA: {
    law: "DPDP Act 2023",
    ref: "Section 10(2)(c)(i)",
    title: "SDF: Data Protection Impact Assessment",
    explanation:
      "Significant Data Fiduciaries must conduct periodic Data Protection Impact Assessments (DPIA) on high-risk processing operations.",
    defaultGuidance:
      "Document formal DPIA assessments for large-scale or algorithmic personal data systems.",
  },
  ACT_SEC_10_AUDIT: {
    law: "DPDP Act 2023",
    ref: "Section 10(2)(c)(ii)",
    title: "SDF: Periodic Compliance Audits",
    explanation:
      "Significant Data Fiduciaries must conduct periodic compliance audits and review internal data protection controls.",
    defaultGuidance:
      "Conduct annual compliance audits to review security, vendor contracts, and consent logs.",
  },
  ACT_SEC_11: {
    law: "DPDP Act 2023",
    ref: "Section 11",
    title: "Right to Information About Personal Data",
    explanation:
      "Users have the right to obtain a summary of their personal data being processed, sharing categories, and third-party identities.",
    defaultGuidance:
      "Provide an accessible portal or data request channel where users can view and request summaries of their personal data.",
  },
  ACT_SEC_12: {
    law: "DPDP Act 2023",
    ref: "Section 12",
    title: "Right to Correction, Updating and Erasure",
    explanation:
      "Users have statutory rights to request correction of inaccurate data, completion of incomplete data, updating of records, and erasure.",
    defaultGuidance:
      "Provide intuitive profile correction and account erasure request mechanisms.",
  },
  ACT_SEC_13: {
    law: "DPDP Act 2023",
    ref: "Section 13",
    title: "Right of Grievance Redressal",
    explanation:
      "Users have the right to register grievances regarding personal data processing and receive a response within a prescribed period.",
    defaultGuidance:
      "Document multi-tiered escalation levels with specific response turnaround times for privacy grievances.",
  },

  // DPDP RULES 2025
  RULE_3: {
    law: "DPDP Rules 2025",
    ref: "Rule 3(a)",
    title: "Standalone Privacy Notice",
    explanation:
      "The privacy notice must be presented and understandable independently of general terms, marketing, or unrelated information.",
    defaultGuidance:
      "Host a dedicated, standalone Privacy Policy page accessible directly via standard navigation.",
  },
  RULE_3_ITEMISED_DATA: {
    law: "DPDP Rules 2025",
    ref: "Rule 3(b)(i)",
    title: "Itemised Personal Data in Notice",
    explanation:
      "The notice must provide an itemised list of each specific category of personal data being collected from the user.",
    defaultGuidance:
      "Itemise all collected data points (e.g., Name, Mobile, Email, Roll No, Aadhaar, IP) in the privacy notice.",
  },
  RULE_3_PURPOSE: {
    law: "DPDP Rules 2025",
    ref: "Rule 3(b)(ii)",
    title: "Specified Purpose Description",
    explanation:
      "The notice must describe the specific processing purposes and the exact services or functions enabled by processing.",
    defaultGuidance:
      "Link each personal data category directly to the specific service or operational purpose it facilitates.",
  },
  RULE_3_LINKS: {
    law: "DPDP Rules 2025",
    ref: "Rule 3(c)",
    title: "Notice Rights and Complaint Links",
    explanation:
      "The notice must include functional communication links for users to withdraw consent, exercise rights, and complain to the Board.",
    defaultGuidance:
      "Include direct clickable links to the grievance portal, rights center, and regulatory ombudsman in the notice.",
  },
  RULE_6_ENCRYPTION: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(a)",
    title: "Data Encryption and Masking",
    explanation:
      "Organizations must implement encryption in transit and at rest, tokenization, or masking to shield sensitive data.",
    defaultGuidance:
      "Ensure HTTPS/TLS encryption across all web traffic and encrypt stored sensitive personal records.",
  },
  RULE_6_ACCESS: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(b)",
    title: "Computer Resource Access Control",
    explanation:
      "Appropriate role-based access controls must restrict computer systems and networks to authorized personnel only.",
    defaultGuidance:
      "Enforce least-privilege password policies, role-based permissions, and network segmentation.",
  },
  RULE_6_LOGGING: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(c)",
    title: "Access Logging and Monitoring",
    explanation:
      "Continuous system logging and monitoring must be maintained to detect, investigate, and remediate unauthorized access.",
    defaultGuidance:
      "Maintain centralized security and access logs for all systems handling personal data.",
  },
  RULE_6_BACKUPS: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(d)",
    title: "Business Continuity and Backups",
    explanation:
      "Organizations must maintain regular data backups and disaster recovery protocols to ensure business continuity.",
    defaultGuidance:
      "Document regular backup schedules and disaster recovery testing procedures.",
  },
  RULE_6_LOG_RETENTION: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(e)",
    title: "One-Year Security Log Retention",
    explanation:
      "Relevant security audit and system access logs must be retained for at least one year for incident investigation purposes.",
    defaultGuidance:
      "Configure log retention policies to preserve system and authentication logs for a minimum of 12 months.",
  },
  RULE_6_PROCESSOR_CONTRACT: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(f)",
    title: "Processor Contract Safeguards",
    explanation:
      "Vendor and processor contracts must legally mandate adherence to reasonable security standards and breach reporting.",
    defaultGuidance:
      "Review third-party contracts to ensure binding security safeguards and incident notification clauses.",
  },
  RULE_6_TECH_ORG: {
    law: "DPDP Rules 2025",
    ref: "Rule 6(1)(g)",
    title: "Technical & Organisational Controls",
    explanation:
      "Organizations must implement comprehensive technical measures (firewalls, anti-virus) and organizational policies.",
    defaultGuidance:
      "Maintain active firewall protections, automated software patch updates, and security training.",
  },
  RULE_7_PRINCIPAL_BREACH: {
    law: "DPDP Rules 2025",
    ref: "Rule 7(1)",
    title: "Breach Notice to Affected Principals",
    explanation:
      "In any data breach, affected individuals must be notified without delay in plain language with safety and contact details.",
    defaultGuidance:
      "Maintain pre-drafted breach communication templates explaining consequences, safety actions, and contact avenues.",
  },
  RULE_7_BOARD_BREACH: {
    law: "DPDP Rules 2025",
    ref: "Rule 7(2)",
    title: "72-Hour Breach Notice to Board",
    explanation:
      "The organization must notify the Data Protection Board without delay, submitting a detailed incident report within 72 hours.",
    defaultGuidance:
      "Establish internal escalation workflows to ensure regulatory intimations within 72 hours of incident confirmation.",
  },
  RULE_8_ERASURE: {
    law: "DPDP Rules 2025",
    ref: "Rule 8(1)",
    title: "Specified-Purpose Erasure Protocol",
    explanation:
      "Personal data must be permanently deleted after the specified purpose expires if the user has had no ongoing activity.",
    defaultGuidance:
      "Implement automatic deletion protocols when account retention thresholds expire.",
  },
  RULE_8_48_HOURS: {
    law: "DPDP Rules 2025",
    ref: "Rule 8(2)",
    title: "48-Hour Pre-Erasure Notice",
    explanation:
      "Organizations must notify users at least 48 hours before scheduled data deletion, giving them an opportunity to keep their account active.",
    defaultGuidance:
      "Configure automated email alerts 48 hours prior to scheduled data or account removal.",
  },
  RULE_8_ONE_YEAR: {
    law: "DPDP Rules 2025",
    ref: "Rule 8(3)",
    title: "One-Year Processing Log Retention",
    explanation:
      "For specified categories of processing, organizations must retain personal and traffic data logs for at least one year before erasure.",
    defaultGuidance:
      "Retain traffic logs and transactional records for 12 months before applying purge cycles.",
  },
  RULE_9_CONTACT: {
    law: "DPDP Rules 2025",
    ref: "Rule 9",
    title: "Published Privacy Contact Details",
    explanation:
      "The organization must prominently publish business contact details of the DPO or privacy officer who can answer data queries.",
    defaultGuidance:
      "Prominently list the Data Protection Officer or Grievance Officer name and contact email in the footer.",
  },
  RULE_10_CHILD_CONSENT: {
    law: "DPDP Rules 2025",
    ref: "Rule 10",
    title: "Child Parental Consent Verification",
    explanation:
      "Organizations processing child data must verify that the consenting person is an identifiable adult using appropriate measures.",
    defaultGuidance:
      "Implement an adult verification check (such as parent ID or signed declaration) before collecting data from minors.",
  },
  RULE_11_GUARDIAN: {
    law: "DPDP Rules 2025",
    ref: "Rule 11",
    title: "Lawful Guardian Verification",
    explanation:
      "Organizations must exercise due diligence to verify that a person claiming to be a legal guardian was duly appointed by a lawful authority.",
    defaultGuidance:
      "Request legal guardianship documentation when processing data on behalf of individuals with disabilities.",
  },
  RULE_13_DPIA: {
    law: "DPDP Rules 2025",
    ref: "Rule 13(1)",
    title: "Annual SDF DPIA and Audit",
    explanation:
      "Significant Data Fiduciaries must carry out a formal Data Protection Impact Assessment and compliance audit every 12 months.",
    defaultGuidance:
      "Conduct annual internal privacy risk assessments and external security audits for SDF entities.",
  },
  RULE_13_BOARD_REPORT: {
    law: "DPDP Rules 2025",
    ref: "Rule 13(2)",
    title: "SDF DPIA Reporting to Board",
    explanation:
      "Significant Data Fiduciaries must submit significant audit and DPIA observations directly to the Data Protection Board.",
    defaultGuidance:
      "File annual audit reports with regulatory authorities if classified as an SDF.",
  },
  RULE_13_ALGORITHMIC_RISK: {
    law: "DPDP Rules 2025",
    ref: "Rule 13(3)",
    title: "SDF Algorithmic Risk Due Diligence",
    explanation:
      "Significant Data Fiduciaries must review automated and algorithmic processing tools to ensure they do not infringe on user rights.",
    defaultGuidance:
      "Review automated decision algorithms for bias and data protection compliance.",
  },
  RULE_13_LOCALISATION: {
    law: "DPDP Rules 2025",
    ref: "Rule 13(4)",
    title: "SDF Data Localisation Compliance",
    explanation:
      "Significant Data Fiduciaries must comply with Government restrictions preventing specified personal data from being transferred outside India.",
    defaultGuidance:
      "Host critical personal data within Indian data center regions in accordance with statutory guidelines.",
  },
  RULE_14_RIGHTS_MEANS: {
    law: "DPDP Rules 2025",
    ref: "Rule 14(1)",
    title: "Published Means to Exercise Rights",
    explanation:
      "The organization must publish explicit means for users to exercise data rights and specify required identity verification details.",
    defaultGuidance:
      "Publish a dedicated rights submission mechanism detailing required identifiers (e.g. registered email or roll number).",
  },
  RULE_14_GRIEVANCE_90_DAYS: {
    law: "DPDP Rules 2025",
    ref: "Rule 14(3)",
    title: "Grievance Response Within 90 Days",
    explanation:
      "The published grievance redressal system must resolve user complaints in a reasonable time frame not exceeding 90 days.",
    defaultGuidance:
      "Document a clear timeline guaranteeing resolution of privacy complaints within 30 to 90 days.",
  },
  RULE_15_CROSS_BORDER: {
    law: "DPDP Rules 2025",
    ref: "Rule 15",
    title: "Cross-Border Transfer Restrictions",
    explanation:
      "Organizations must comply with all Central Government notifications restricting transfer of personal data to foreign entities.",
    defaultGuidance:
      "Verify that cloud data hosting and third-party vendors comply with Indian cross-border transfer directives.",
  },
};

// Helper to obtain standardized title
export function getActTitle(finding) {
  const rid = finding?.requirement_id;
  const meta = DPDP_ACT_METADATA[rid];
  if (meta?.title) return meta.title;
  if (finding?.requirement_title) return finding.requirement_title;
  return finding?.requirement || rid || "Statutory Requirement";
}

// Helper to obtain legal reference (e.g. Section 4, Rule 6(1))
export function getActRef(finding) {
  const rid = finding?.requirement_id;
  const meta = DPDP_ACT_METADATA[rid];
  if (meta?.ref) return meta.ref;
  if (finding?.legal_reference) return finding.legal_reference;
  if (rid?.startsWith("ACT_SEC_")) {
    const sec = rid.replace("ACT_SEC_", "").replace("_", ".");
    return `Section ${sec}`;
  }
  if (rid?.startsWith("RULE_")) {
    const r = rid.replace("RULE_", "").replace("_", ".");
    return `Rule ${r}`;
  }
  return "Provision";
}

// Helper to get Law name badge (DPDP Act 2023 vs DPDP Rules 2025)
export function getActLawBadge(finding) {
  const rid = finding?.requirement_id || "";
  const meta = DPDP_ACT_METADATA[rid];
  if (meta?.law) return meta.law;
  if (rid.startsWith("RULE_")) return "DPDP Rules 2025";
  return "DPDP Act 2023";
}

// 1. Act Explanation (Concise plain English)
export function getShortActExplanation(finding) {
  const rid = finding?.requirement_id;
  const meta = DPDP_ACT_METADATA[rid];
  if (meta?.explanation) return meta.explanation;
  if (finding?.requirement) return finding.requirement;
  return "The organization must observe statutory personal data protection principles under Indian law.";
}

// 2. Semantic Reasoning & Evaluation (Short crisp assessment verdict)
export function getShortReasoning(finding) {
  const raw = String(finding?.explanation || "").trim();
  const status = finding?.status;

  if (status === "compliant") {
    if (raw && !raw.includes("Deterministic evaluation")) {
      return raw.length > 200 ? raw.slice(0, 197) + "..." : raw;
    }
    return "The scanner verified that the website satisfies this requirement based on observable policy and operational disclosures.";
  }

  if (status === "partially_compliant") {
    if (raw && !raw.includes("Deterministic evaluation")) {
      return raw.length > 200 ? raw.slice(0, 197) + "..." : raw;
    }
    return "Partial evidence discovered: key core safeguards are in place, but some specific statutory elements remain unconfirmed.";
  }

  if (status === "non_compliant") {
    return raw || "Website practices directly contradict statutory requirements under the DPDP framework.";
  }

  return "No observable website disclosures or implementation evidence was discovered for this provision during the screening.";
}

// 3. Compliance Guidance (Short actionable next step)
export function getShortGuidance(finding) {
  const raw = String(finding?.recommendation || "").trim();
  const rid = finding?.requirement_id;
  const meta = DPDP_ACT_METADATA[rid];
  const status = finding?.status;

  if (status === "compliant") {
    return "No remediation required based on current website screening disclosures. Maintain ongoing monitoring.";
  }

  if (raw && raw !== "No action required based on the available website evidence." && !raw.includes("Collect additional")) {
    return raw.length > 180 ? raw.slice(0, 177) + "..." : raw;
  }

  if (meta?.defaultGuidance) {
    return meta.defaultGuidance;
  }

  return "Update public privacy documentation or online portals to explicitly address this requirement.";
}

// 4. Evidence Cleaner (Real-scanner presentation)
export function extractCleanEvidence(evidence) {
  if (!evidence) return null;

  let parsed = evidence;
  if (typeof evidence === "string") {
    try {
      parsed = JSON.parse(evidence);
    } catch {
      return {
        type: "raw",
        text: evidence.trim(),
      };
    }
  }

  if (!parsed || typeof parsed !== "object") {
    return null;
  }

  // If detected_elements list exists
  if (Array.isArray(parsed.detected_elements) && parsed.detected_elements.length > 0) {
    const elements = parsed.detected_elements.map((el) => {
      const name = String(el.element || "")
        .replaceAll("_", " ")
        .replace(/\b\w/g, (c) => c.toUpperCase());
      const quotes = Array.isArray(el.evidence) ? el.evidence : [];
      let quote = quotes.length > 0 ? String(quotes[0]).trim() : "";
      if (quote.length > 280) quote = quote.slice(0, 277) + "...";
      
      const fields = Array.isArray(el.matched_fields) ? el.matched_fields : [];
      const sources = fields.map((f) =>
        f
          .replaceAll("_", " ")
          .replace(/\b\w/g, (c) => c.toUpperCase())
      );

      return {
        name,
        quote,
        sources,
        status: el.status || "sufficient",
      };
    });

    return {
      type: "elements",
      items: elements,
    };
  }

  // Fallback stringified object if non-empty
  const keys = Object.keys(parsed);
  if (keys.length === 0) return null;

  const keyPreviews = [];
  for (const k of keys.slice(0, 3)) {
    const val = parsed[k];
    if (typeof val === "string" && val.trim()) {
      keyPreviews.push({
        name: k.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase()),
        quote: val.trim().slice(0, 250),
        sources: [k],
      });
    }
  }

  if (keyPreviews.length > 0) {
    return {
      type: "elements",
      items: keyPreviews,
    };
  }

  return null;
}
