import {
  getActTitle,
  getActRef,
  getActLawBadge,
  getShortActExplanation,
  getShortReasoning,
  getShortGuidance,
  extractCleanEvidence,
} from "./dpdpActData";

function getCleanDomain(url) {
  if (!url) return "target-domain";
  try {
    let clean = url.trim();
    if (!/^https?:\/\//i.test(clean)) clean = "https://" + clean;
    const parsed = new URL(clean);
    return parsed.hostname.replace(/^www\./, "").replace(/[^a-zA-Z0-9.-]/g, "_");
  } catch {
    return url.replace(/[^a-zA-Z0-9.-]/g, "_").slice(0, 30);
  }
}

function getFormattedDate() {
  const d = new Date();
  return d.toISOString().split("T")[0];
}

function getFormattedDateTime() {
  const d = new Date();
  return d.toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function getStatusBadgeData(status) {
  switch (status) {
    case "compliant":
      return { label: "COMPLIANT", color: "#059669", bg: "#ecfdf5", border: "#a7f3d0", icon: "✓" };
    case "partially_compliant":
      return { label: "PARTIALLY COMPLIANT", color: "#d97706", bg: "#fffbeb", border: "#fde68a", icon: "⚠" };
    case "non_compliant":
      return { label: "NON-COMPLIANT", color: "#dc2626", bg: "#fef2f2", border: "#fecaca", icon: "✕" };
    case "insufficient_evidence":
      return { label: "INSUFFICIENT EVIDENCE", color: "#4b5563", bg: "#f3f4f6", border: "#e5e7eb", icon: "—" };
    case "future_requirement":
      return { label: "FUTURE REQUIREMENT", color: "#7c3aed", bg: "#f5f3ff", border: "#ddd6fe", icon: "⏳" };
    default:
      return { label: (status || "N/A").toUpperCase().replaceAll("_", " "), color: "#4b5563", bg: "#f3f4f6", border: "#e5e7eb", icon: "•" };
  }
}

function formatEvidenceText(evidence) {
  const clean = extractCleanEvidence(evidence);
  if (!clean) {
    return "No direct website disclosures discovered. (Internal governance control or unobservable on public web pages).";
  }
  if (clean.type === "elements" && clean.items?.length > 0) {
    return clean.items
      .map((it) => {
        let str = `• ${it.name}`;
        if (it.sources && it.sources.length > 0) str += ` [Source: ${it.sources.join(", ")}]`;
        if (it.quote) str += `: "${it.quote}"`;
        return str;
      })
      .join("\n");
  }
  if (clean.type === "raw" && clean.text) {
    return `"${clean.text}"`;
  }
  return "No direct website disclosures discovered.";
}

// ==========================================
// 1. CSV EXPORT
// ==========================================
export function downloadCsvReport(report, websiteUrl) {
  if (!report) return;
  const targetDomain = report.website || websiteUrl || "Target";
  const findings = report?.compliance?.findings || [];

  const headers = [
    "Requirement ID",
    "Law Framework",
    "Section / Rule",
    "Requirement Title",
    "Compliance Status",
    "Statutory Legal Mandate",
    "AI Evaluation & Semantic Reasoning",
    "Actionable Remediation Guidance",
    "Discovered Website Evidence",
  ];

  const rows = findings.map((f, idx) => {
    const reqId = f.requirement_id || `REQ-${idx + 1}`;
    const law = getActLawBadge(f);
    const ref = getActRef(f);
    const title = getActTitle(f);
    const status = getStatusBadgeData(f.status).label;
    const mandate = getShortActExplanation(f);
    const reasoning = getShortReasoning(f);
    const guidance = getShortGuidance(f);
    const evidenceText = formatEvidenceText(f.evidence);

    return [
      reqId,
      law,
      ref,
      title,
      status,
      mandate,
      reasoning,
      guidance,
      evidenceText,
    ].map((val) => `"${String(val || "").replace(/"/g, '""')}"`);
  });

  const csvContent =
    "\uFEFF" + [headers.join(","), ...rows.map((r) => r.join(","))].join("\r\n");

  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `DPDP_Compliance_Matrix_${getCleanDomain(targetDomain)}_${getFormattedDate()}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ==========================================
// 2. JSON EXPORT
// ==========================================
export function downloadJsonReport(report, websiteUrl) {
  if (!report) return;
  const targetDomain = report.website || websiteUrl || "Target";

  const exportPayload = {
    metadata: {
      tool: "DPDP Compliance Intelligence",
      statute: "Digital Personal Data Protection Act, 2023 & DPDP Rules, 2025",
      target_website: targetDomain,
      generated_at: new Date().toISOString(),
      assessment_regime: report?.compliance?.assessment_date || "2027-01-01",
      sector_category: report?.classification?.category || "General",
    },
    scoring: report?.compliance?.scoring || report?.compliance?.score || {},
    findings: (report?.compliance?.findings || []).map((f) => ({
      requirement_id: f.requirement_id,
      law: getActLawBadge(f),
      section_ref: getActRef(f),
      title: getActTitle(f),
      status: f.status,
      statutory_mandate: getShortActExplanation(f),
      ai_reasoning: getShortReasoning(f),
      remediation_guidance: getShortGuidance(f),
      evidence_summary: extractCleanEvidence(f.evidence),
      raw_evidence: f.evidence,
    })),
    raw_analysis: report,
  };

  const jsonStr = JSON.stringify(exportPayload, null, 2);
  const blob = new Blob([jsonStr], { type: "application/json;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `DPDP_Audit_Report_${getCleanDomain(targetDomain)}_${getFormattedDate()}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ==========================================
// 3. HTML REPORT GENERATION (PRINT / PDF / STANDALONE)
// ==========================================
export function generateReportHtml(report, websiteUrl) {
  if (!report) return "";
  const targetDomain = report.website || websiteUrl || "Target Website";
  const scoring = report?.compliance?.scoring || report?.compliance?.score || {};
  const classification = report?.classification;
  const findings = report?.compliance?.findings || [];
  const complianceScore = scoring.score != null ? scoring.score : "N/A";
  const evidenceCoverage =
    scoring.evidence_coverage_display ??
    (scoring.evidence_coverage != null ? `${scoring.evidence_coverage}%` : "N/A");
  const assessmentDate = report?.compliance?.assessment_date || "2027-01-01";
  const generatedTime = getFormattedDateTime();

  const scoreNum = Number(scoring.score);
  const scoreColor = scoreNum >= 80 ? "#059669" : scoreNum >= 50 ? "#d97706" : "#dc2626";

  const findingsHtml = findings
    .map((f, idx) => {
      const badge = getStatusBadgeData(f.status);
      const lawBadge = getActLawBadge(f);
      const isRules = lawBadge.includes("Rules");
      const ref = getActRef(f);
      const title = getActTitle(f);
      const explanation = getShortActExplanation(f);
      const reasoning = getShortReasoning(f);
      const guidance = getShortGuidance(f);
      const cleanEvidence = extractCleanEvidence(f.evidence);

      let evidenceContentHtml = '<div style="color: #6b7280; font-style: italic;">No direct website disclosures discovered. (Internal governance control or unobservable on public pages).</div>';
      if (cleanEvidence?.type === "elements" && cleanEvidence.items?.length > 0) {
        evidenceContentHtml = cleanEvidence.items
          .map(
            (it) => `
          <div style="background: #f8fafc; border-left: 3px solid #6366f1; padding: 8px 12px; margin-bottom: 6px; border-radius: 4px;">
            <div style="font-weight: 700; font-size: 12px; color: #3730a3;">✓ ${it.name} ${
              it.sources?.length ? `<span style="font-weight: 500; font-size: 10px; color: #6b7280; background: #e0e7ff; padding: 2px 6px; border-radius: 4px; margin-left: 4px;">${it.sources.join(", ")}</span>` : ""
            }</div>
            ${it.quote ? `<div style="font-size: 12px; color: #475569; margin-top: 4px; font-style: italic;">"${it.quote}"</div>` : ""}
          </div>`
          )
          .join("");
      } else if (cleanEvidence?.type === "raw" && cleanEvidence.text) {
        evidenceContentHtml = `<div style="font-size: 12px; color: #475569; font-style: italic; background: #f8fafc; padding: 8px 12px; border-radius: 4px; border-left: 3px solid #6366f1;">"${cleanEvidence.text}"</div>`;
      }

      return `
      <div class="finding-card">
        <div class="finding-header">
          <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
            <span class="law-pill ${isRules ? "rules-pill" : "act-pill"}">${lawBadge}</span>
            <span class="ref-pill">${ref}</span>
            <span class="finding-title">${title}</span>
          </div>
          <span class="status-pill" style="color: ${badge.color}; background: ${badge.bg}; border: 1px solid ${badge.border};">
            ${badge.icon} ${badge.label}
          </span>
        </div>
        <div class="finding-grid">
          <div class="quad-box">
            <div class="quad-title">📜 Statutory Legal Mandate</div>
            <div class="quad-content">${explanation}</div>
          </div>
          <div class="quad-box">
            <div class="quad-title">🧠 AI Evaluation & Semantic Reasoning</div>
            <div class="quad-content">${reasoning}</div>
          </div>
          <div class="quad-box">
            <div class="quad-title">💡 Actionable Remediation Guidance</div>
            <div class="quad-content">${guidance}</div>
          </div>
          <div class="quad-box">
            <div class="quad-title">🔍 Discovered Website Evidence</div>
            <div class="quad-content">${evidenceContentHtml}</div>
          </div>
        </div>
      </div>
      `;
    })
    .join("");

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>DPDP Compliance Audit Report - ${targetDomain}</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');
    
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      background-color: #ffffff;
      color: #0f172a;
      line-height: 1.5;
      padding: 30px;
    }
    .report-wrapper {
      max-width: 960px;
      margin: 0 auto;
    }
    .header-bar {
      border-bottom: 2px solid #0f172a;
      padding-bottom: 18px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 16px;
    }
    .gov-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: #eef2ff;
      color: #4338ca;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.05em;
      padding: 4px 12px;
      border-radius: 14px;
      border: 1px solid #c7d2fe;
      margin-bottom: 8px;
      text-transform: uppercase;
    }
    .main-title {
      font-size: 26px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.02em;
      margin-bottom: 4px;
    }
    .sub-title {
      font-size: 13px;
      color: #475569;
    }
    .target-badge-block {
      text-align: right;
      font-size: 12px;
      color: #64748b;
    }
    .target-domain {
      font-family: 'JetBrains Mono', monospace;
      font-size: 16px;
      font-weight: 700;
      color: #0284c7;
      background: #f0f9ff;
      padding: 4px 10px;
      border-radius: 6px;
      border: 1px solid #bae6fd;
      display: inline-block;
      margin-top: 4px;
    }
    .score-cards-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 24px;
    }
    .metric-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 16px 20px;
    }
    .metric-label {
      font-size: 11px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .metric-val {
      font-size: 34px;
      font-weight: 800;
      margin: 6px 0;
      letter-spacing: -0.02em;
    }
    .metric-sub {
      font-size: 12px;
      color: #64748b;
    }
    .summary-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 18px 22px;
      margin-bottom: 24px;
    }
    .summary-title {
      font-size: 15px;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 6px;
    }
    .summary-text {
      font-size: 13px;
      color: #475569;
      line-height: 1.5;
      margin-bottom: 16px;
    }
    .breakdown-row {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 10px;
    }
    .breakdown-pill {
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 10px 14px;
    }
    .breakdown-count {
      font-size: 20px;
      font-weight: 800;
    }
    .breakdown-label {
      font-size: 11px;
      font-weight: 600;
      color: #64748b;
      margin-top: 2px;
    }
    .findings-header-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin: 28px 0 14px 0;
      border-bottom: 1px solid #e2e8f0;
      padding-bottom: 8px;
    }
    .findings-heading {
      font-size: 18px;
      font-weight: 800;
      color: #0f172a;
    }
    .findings-counter {
      font-size: 12px;
      color: #64748b;
      font-weight: 600;
    }
    .finding-card {
      border: 1px solid #e2e8f0;
      border-radius: 10px;
      margin-bottom: 14px;
      background: #ffffff;
      overflow: hidden;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    .finding-header {
      background: #f8fafc;
      padding: 12px 16px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      border-bottom: 1px solid #e2e8f0;
    }
    .law-pill {
      font-size: 10px;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .act-pill {
      background: #e0f2fe;
      color: #0369a1;
      border: 1px solid #bae6fd;
    }
    .rules-pill {
      background: #f3e8ff;
      color: #7e22ce;
      border: 1px solid #e9d5ff;
    }
    .ref-pill {
      font-family: 'JetBrains Mono', monospace;
      font-size: 11px;
      font-weight: 600;
      background: #ffffff;
      color: #475569;
      border: 1px solid #cbd5e1;
      padding: 2px 7px;
      border-radius: 4px;
    }
    .finding-title {
      font-size: 13px;
      font-weight: 700;
      color: #0f172a;
    }
    .status-pill {
      font-size: 11px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 6px;
      white-space: nowrap;
    }
    .finding-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
      padding: 14px 16px;
    }
    .quad-box {
      font-size: 12px;
      line-height: 1.5;
    }
    .quad-title {
      font-size: 10px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #64748b;
      margin-bottom: 4px;
    }
    .quad-content {
      color: #1e293b;
    }
    .disclaimer-box {
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 10px;
      padding: 14px 18px;
      font-size: 11px;
      color: #92400e;
      margin-top: 30px;
      line-height: 1.5;
      page-break-inside: avoid;
    }
    .footer-bar {
      margin-top: 20px;
      border-top: 1px solid #e2e8f0;
      padding-top: 12px;
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: #94a3b8;
    }
    
    @media print {
      body {
        padding: 0;
        background: #ffffff;
      }
      .report-wrapper {
        max-width: 100%;
      }
      .no-print {
        display: none !important;
      }
      .finding-card {
        page-break-inside: avoid;
        break-inside: avoid;
      }
      @page {
        margin: 15mm;
        size: A4 portrait;
      }
    }
  </style>
</head>
<body>
  <div class="report-wrapper">
    <!-- Top Action Bar (hidden on print) -->
    <div class="no-print" style="margin-bottom: 20px; display: flex; justify-content: flex-end; gap: 10px;">
      <button onclick="window.print()" style="background: #2563eb; color: #ffffff; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 700; font-size: 13px; cursor: pointer; display: inline-flex; alignItems: center; gap: 6px;">
        🖨️ Print or Save as PDF
      </button>
    </div>

    <!-- Header -->
    <div class="header-bar">
      <div>
        <div class="gov-pill">⚖ Statutory Compliance Screening • Official Audit Report</div>
        <h1 class="main-title">Digital Personal Data Protection Act, 2023</h1>
        <div class="sub-title">Automated Technical & Evidence Discovery Assessment (DPDP Rules, 2025 Framework)</div>
      </div>
      <div class="target-badge-block">
        <div>Target Website Audited</div>
        <div class="target-domain">${targetDomain}</div>
        <div style="margin-top: 4px;">Sector: <strong>${(classification?.category || "General").toUpperCase()}</strong></div>
        <div>Date: <strong>${generatedTime}</strong></div>
      </div>
    </div>

    <!-- Key Metrics Cards -->
    <div class="score-cards-row">
      <div class="metric-card" style="border-top: 3px solid ${scoreColor};">
        <div class="metric-label">Statutory Compliance Score</div>
        <div class="metric-val" style="color: ${scoreColor};">${complianceScore}%</div>
        <div class="metric-sub">Assessed among ${scoring.total_scoreable ?? 0} scoreable provisions</div>
      </div>
      <div class="metric-card" style="border-top: 3px solid #0284c7;">
        <div class="metric-label">Evidence Coverage Ratio</div>
        <div class="metric-val" style="color: #0284c7;">${evidenceCoverage}</div>
        <div class="metric-sub">${scoring.total_scoreable ?? 0} of ${scoring.total_currently_applicable ?? 47} applicable requirements verified</div>
      </div>
      <div class="metric-card" style="border-top: 3px solid #7c3aed;">
        <div class="metric-label">Enforcement Regime</div>
        <div class="metric-val" style="color: #7c3aed; font-size: 22px; line-height: 1.4;">Rules 2025 (Phased)</div>
        <div class="metric-sub">Simulated Post-Commencement (${assessmentDate})</div>
      </div>
    </div>

    <!-- Summary Card -->
    <div class="summary-card">
      <div class="summary-title">Executive Audit Summary</div>
      <div class="summary-text">${scoring.message || "Automated statutory audit completed."}</div>
      <div class="breakdown-row">
        <div class="breakdown-pill" style="border-left: 3px solid #059669;">
          <div class="breakdown-count" style="color: #059669;">${scoring.compliant ?? 0}</div>
          <div class="breakdown-label">Fully Compliant</div>
        </div>
        <div class="breakdown-pill" style="border-left: 3px solid #d97706;">
          <div class="breakdown-count" style="color: #d97706;">${scoring.partially_compliant ?? 0}</div>
          <div class="breakdown-label">Partially Compliant</div>
        </div>
        <div class="breakdown-pill" style="border-left: 3px solid #dc2626;">
          <div class="breakdown-count" style="color: #dc2626;">${scoring.non_compliant ?? 0}</div>
          <div class="breakdown-label">Non-Compliant</div>
        </div>
        <div class="breakdown-pill" style="border-left: 3px solid #4b5563;">
          <div class="breakdown-count" style="color: #4b5563;">${scoring.insufficient_evidence ?? 0}</div>
          <div class="breakdown-label">Insufficient Evidence</div>
        </div>
      </div>
    </div>

    <!-- Findings Section -->
    <div class="findings-header-row">
      <div class="findings-heading">Statutory Requirement Findings & Evidence</div>
      <div class="findings-counter">Showing ${findings.length} evaluated provisions</div>
    </div>

    ${findingsHtml}

    <!-- Disclaimer -->
    <div class="disclaimer-box">
      <strong>Statutory Compliance Screening Disclaimer:</strong><br />
      This automated compliance assessment is an evidence-based technical screening of publicly observable website elements under India's Digital Personal Data Protection Act, 2023 and DPDP Rules, 2025. Public website evidence cannot verify internal organizational controls, confidential vendor contracts, or backend security configurations. This technical screening does not constitute legal counsel or a definitive statutory certification.
    </div>

    <!-- Footer -->
    <div class="footer-bar">
      <div>Generated by DPDP Compliance Intelligence AI Engine</div>
      <div>Audit Date: ${generatedTime} • Assessment Framework: DPDP Act 2023 & Rules 2025</div>
    </div>
  </div>
</body>
</html>`;
}

// ==========================================
// 4. PRINT / SAVE AS PDF VIA HIDDEN IFRAME
// ==========================================
export function printPdfReport(report, websiteUrl) {
  if (!report) return;
  const htmlContent = generateReportHtml(report, websiteUrl);

  const iframe = document.createElement("iframe");
  iframe.style.position = "fixed";
  iframe.style.right = "0";
  iframe.style.bottom = "0";
  iframe.style.width = "0";
  iframe.style.height = "0";
  iframe.style.border = "none";
  document.body.appendChild(iframe);

  const doc = iframe.contentWindow.document;
  doc.open();
  doc.write(htmlContent);
  doc.close();

  iframe.onload = () => {
    setTimeout(() => {
      try {
        iframe.contentWindow.focus();
        iframe.contentWindow.print();
      } catch (err) {
        console.error("Print execution failed, falling back to popup window:", err);
        const win = window.open("", "_blank");
        win.document.write(htmlContent);
        win.document.close();
        win.focus();
        win.print();
      } finally {
        setTimeout(() => {
          document.body.removeChild(iframe);
        }, 3000);
      }
    }, 400);
  };
}

// ==========================================
// 5. DOWNLOAD STANDALONE HTML REPORT
// ==========================================
export function downloadHtmlReport(report, websiteUrl) {
  if (!report) return;
  const targetDomain = report.website || websiteUrl || "Target";
  const htmlContent = generateReportHtml(report, websiteUrl);

  const blob = new Blob([htmlContent], { type: "text/html;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `DPDP_Audit_Report_${getCleanDomain(targetDomain)}_${getFormattedDate()}.html`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
