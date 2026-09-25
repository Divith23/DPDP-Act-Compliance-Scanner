import React, { useState } from "react";
import ModernScanProgress from "./ScanProgress";
import {
  DPDP_ACT_METADATA,
  getActTitle,
  getActRef,
  getActLawBadge,
  getShortActExplanation,
  getShortReasoning,
  getShortGuidance,
  extractCleanEvidence,
} from "./dpdpActData";
import {
  printPdfReport,
  downloadHtmlReport,
  downloadCsvReport,
  downloadJsonReport,
} from "./reportGenerator";

const CRAWLER_API = "http://127.0.0.1:8080";
const BACKEND_API = "http://127.0.0.1:8081";

function getStatusBadgeStyle(status) {
  switch (status) {
    case "compliant":
      return {
        background: "rgba(13, 148, 136, 0.12)",
        color: "#0f766e",
        border: "1px solid rgba(13, 148, 136, 0.35)",
        boxShadow: "0 1px 4px rgba(13, 148, 136, 0.08)",
      };
    case "partially_compliant":
      return {
        background: "rgba(217, 119, 6, 0.12)",
        color: "#b45309",
        border: "1px solid rgba(217, 119, 6, 0.35)",
        boxShadow: "0 1px 4px rgba(217, 119, 6, 0.08)",
      };
    case "non_compliant":
      return {
        background: "rgba(225, 29, 72, 0.1)",
        color: "#be123c",
        border: "1px solid rgba(225, 29, 72, 0.3)",
      };
    case "insufficient_evidence":
      return {
        background: "rgba(100, 116, 139, 0.1)",
        color: "#475569",
        border: "1px solid rgba(100, 116, 139, 0.25)",
      };
    case "future_requirement":
      return {
        background: "rgba(212, 175, 55, 0.15)",
        color: "#854d0e",
        border: "1px solid rgba(212, 175, 55, 0.4)",
      };
    case "not_applicable":
      return {
        background: "rgba(148, 163, 184, 0.15)",
        color: "#64748b",
        border: "1px solid rgba(148, 163, 184, 0.3)",
      };
    default:
      return {
        background: "rgba(148, 163, 184, 0.15)",
        color: "#475569",
        border: "1px solid rgba(148, 163, 184, 0.3)",
      };
  }
}

function formatStatusBadgeText(status) {
  switch (status) {
    case "compliant":
      return "✓ Compliant";
    case "partially_compliant":
      return "⚠ Partially Compliant";
    case "non_compliant":
      return "✕ Non-Compliant";
    case "insufficient_evidence":
      return "— Insufficient Evidence";
    case "future_requirement":
      return "⏳ Future Requirement";
    case "not_applicable":
      return "Not Applicable";
    default:
      return status ? status.replaceAll("_", " ") : "N/A";
  }
}

function renderCleanEvidenceView(cleanEvidence) {
  if (!cleanEvidence) {
    return (
      <div style={styles.evidenceEmptyBox}>
        <div style={{ color: "#64748b", fontWeight: "500" }}>
          — No direct website disclosures discovered.
        </div>
        <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px" }}>
          Internal governance control or not observable on public web pages.
        </div>
      </div>
    );
  }

  if (cleanEvidence.type === "elements" && cleanEvidence.items?.length > 0) {
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
        {cleanEvidence.items.slice(0, 2).map((item, idx) => (
          <div key={idx} style={styles.evidenceElementRow}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", flexWrap: "wrap" }}>
              <span style={styles.evidenceElementName}>✓ {item.name}</span>
              {item.sources && item.sources.length > 0 && (
                <span style={styles.evidenceSourceTag}>{item.sources.join(", ")}</span>
              )}
            </div>
            {item.quote && (
              <div style={styles.evidenceQuoteText}>
                "{item.quote}"
              </div>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (cleanEvidence.type === "raw" && cleanEvidence.text) {
    return (
      <div style={styles.evidenceQuoteText}>
        "{cleanEvidence.text.length > 250 ? cleanEvidence.text.slice(0, 247) + "..." : cleanEvidence.text}"
      </div>
    );
  }

  return (
    <div style={styles.evidenceEmptyBox}>
      <div style={{ color: "#64748b" }}>— No direct website disclosures discovered.</div>
    </div>
  );
}

function isValidUrl(urlString) {
  if (!urlString || typeof urlString !== "string") return false;
  const trimmed = urlString.trim();
  if (!trimmed || /\s/.test(trimmed)) return false;

  // Reject unsupported protocols like ftp://, file://, etc.
  if (/^[a-zA-Z0-9_-]+:\/\//i.test(trimmed) && !/^https?:\/\//i.test(trimmed)) {
    return false;
  }

  let urlToTest = trimmed;
  if (!/^https?:\/\//i.test(urlToTest)) {
    urlToTest = "https://" + urlToTest;
  }

  try {
    const parsed = new URL(urlToTest);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return false;
    }
    const host = parsed.hostname;
    if (!host || host.length < 3) return false;
    if (host.startsWith(".") || host.endsWith(".") || host.startsWith("-") || host.endsWith("-")) {
      return false;
    }
    // Allow localhost and valid IPv4 addresses
    if (host === "localhost" || /^(\d{1,3}\.){3}\d{1,3}$/.test(host)) {
      return true;
    }
    // Standard domain validation: must contain dot and valid domain characters
    if (!host.includes(".")) {
      return false;
    }
    if (!/^[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$/.test(host)) {
      return false;
    }
    const parts = host.split(".");
    const tld = parts[parts.length - 1];
    if (!/^[a-zA-Z]{2,}$/.test(tld)) {
      return false;
    }
    return true;
  } catch {
    return false;
  }
}

function normalizeUrl(urlString) {
  let trimmed = urlString.trim();
  if (!/^https?:\/\//i.test(trimmed)) {
    trimmed = "https://" + trimmed;
  }
  return trimmed;
}

function App() {
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [scanId, setScanId] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [scanStep, setScanStep] = useState(0);
  const [isPhaseTwo, setIsPhaseTwo] = useState(false);
  const [activeScanningUrl, setActiveScanningUrl] = useState("");
  const [stage, setStage] = useState("");
  const [error, setError] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedIds, setExpandedIds] = useState(new Set());
  const [showInvalidUrlModal, setShowInvalidUrlModal] = useState(false);
  const [invalidUrlReason, setInvalidUrlReason] = useState("");
  const [showReportModal, setShowReportModal] = useState(false);
  const [downloadNotice, setDownloadNotice] = useState("");

  function triggerInvalidUrlPopup(reason = "") {
    setInvalidUrlReason(
      reason ||
        "The entered address is not a valid website URL. Please enter a valid website URL."
    );
    setShowInvalidUrlModal(true);
    setLoading(false);
    setStage("");
  }

  // Handle ESC or Enter key to dismiss invalid URL popup
  React.useEffect(() => {
    if (!showInvalidUrlModal) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape" || e.key === "Enter") {
        setShowInvalidUrlModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showInvalidUrlModal]);

  // Handle ESC key to dismiss report generator modal
  React.useEffect(() => {
    if (!showReportModal) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") {
        setShowReportModal(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [showReportModal]);

  async function scanWebsite(targetUrl) {
    const rawInput = (targetUrl || websiteUrl).trim();
    if (!rawInput) {
      triggerInvalidUrlPopup("Please enter a website URL in the input tab before scanning.");
      return;
    }

    if (!isValidUrl(rawInput)) {
      triggerInvalidUrlPopup(
        `"${rawInput}" is not a valid website URL. Please enter a valid website address.`
      );
      return;
    }

    const inputVal = normalizeUrl(rawInput);

    setLoading(true);
    setError("");
    setReport(null);
    setScanId("");
    setFilterStatus("all");
    setSearchTerm("");
    setScanStep(0);
    setIsPhaseTwo(false);
    setActiveScanningUrl(inputVal);

    let phaseTimer = null;

    try {
      // PHASE 1: Web Crawling & Forensic Discovery (Steps 0 to 5)
      // Smoothly advance steps continuously during crawl execution
      phaseTimer = setInterval(() => {
        setScanStep((prev) => (prev < 5 ? prev + 1 : prev));
      }, 1600);

      const crawlResponse = await fetch(`${CRAWLER_API}/crawl`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          url: inputVal,
        }),
      });

      const crawlData = await crawlResponse.json();

      if (!crawlResponse.ok) {
        throw new Error(crawlData.detail || "Website crawling failed.");
      }

      if (!crawlData.scan_id) {
        throw new Error(
          crawlData.detail ||
            `Could not crawl ${inputVal}. The target website failed to load, timed out, or refused connection.`
        );
      }

      // Phase 1 finished! Complete all crawler steps and initiate Phase 2
      clearInterval(phaseTimer);
      const targetScanId = crawlData.scan_id;
      setScanId(targetScanId);

      setIsPhaseTwo(true);
      setScanStep(6); // Step 7: Classification & Legal RAG

      // PHASE 2: DPDP AI & Legal Compliance Evaluation (Steps 6 to 9)
      phaseTimer = setInterval(() => {
        setScanStep((prev) => (prev < 9 ? prev + 1 : prev));
      }, 1800);

      const analysisResponse = await fetch(
        `${BACKEND_API}/api/analyze/${encodeURIComponent(
          targetScanId
        )}?assessment_date=2027-01-01`
      );

      const analysisData = await analysisResponse.json();

      if (!analysisResponse.ok) {
        throw new Error(analysisData.detail || "Compliance analysis failed.");
      }

      clearInterval(phaseTimer);
      setScanStep(9); // All 10 statutory verification steps completed!

      // Brief transition delay so user sees 100% verified status
      await new Promise((resolve) => setTimeout(resolve, 600));

      setReport(analysisData);

      // Automatically open the first finding for an immediate real-scanner preview
      const initialFindings = analysisData?.compliance?.findings || [];
      if (initialFindings.length > 0) {
        setExpandedIds(new Set([initialFindings[0].requirement_id || "item-0"]));
      }
    } catch (err) {
      if (phaseTimer) clearInterval(phaseTimer);
      console.error(err);
      const errMsg = err.message || "An error occurred during scanning.";
      setError(errMsg);
      if (
        errMsg.toLowerCase().includes("could not crawl") ||
        errMsg.toLowerCase().includes("failed to load") ||
        errMsg.toLowerCase().includes("refused") ||
        errMsg.toLowerCase().includes("timed out") ||
        errMsg.toLowerCase().includes("crawling failed")
      ) {
        triggerInvalidUrlPopup(`Unable to reach "${inputVal}". The website failed to load, timed out, or refused connection.`);
      }
    } finally {
      if (phaseTimer) clearInterval(phaseTimer);
      setLoading(false);
    }
  }

  const compliance = report?.compliance;
  const scoring = compliance?.scoring || compliance?.score || {};
  const classification = report?.classification;
  const findings = compliance?.findings || [];

  const toggleExpand = (id) => {
    setExpandedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const expandAll = () => {
    const all = new Set(filteredFindings.map((f, i) => f.requirement_id || `item-${i}`));
    setExpandedIds(all);
  };

  const collapseAll = () => {
    setExpandedIds(new Set());
  };

  const filteredFindings = findings.filter((f) => {
    // Status filter
    if (filterStatus === "scoreable") {
      if (f.status !== "compliant" && f.status !== "partially_compliant") return false;
    } else if (filterStatus !== "all") {
      if (f.status !== filterStatus) return false;
    }

    // Search filter
    if (searchTerm.trim()) {
      const q = searchTerm.toLowerCase().trim();
      const title = getActTitle(f).toLowerCase();
      const ref = getActRef(f).toLowerCase();
      const law = getActLawBadge(f).toLowerCase();
      const id = (f.requirement_id || "").toLowerCase();
      const req = (f.requirement || "").toLowerCase();
      return (
        title.includes(q) ||
        ref.includes(q) ||
        law.includes(q) ||
        id.includes(q) ||
        req.includes(q)
      );
    }

    return true;
  });

  return (
    <div style={styles.page}>
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes fadeIn {
          from { opacity: 0; }
          to { opacity: 1; }
        }
        @keyframes modalSlideUp {
          from {
            opacity: 0;
            transform: scale(0.95) translateY(12px);
          }
          to {
            opacity: 1;
            transform: scale(1) translateY(0);
          }
        }
      `}</style>

      {/* POPUP MODAL: INVALID WEBSITE URL */}
      {showInvalidUrlModal && (
        <div
          id="invalid-url-modal-backdrop"
          style={styles.modalBackdrop}
          onClick={() => setShowInvalidUrlModal(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="invalid-url-modal-title"
        >
          <div
            id="invalid-url-modal-card"
            style={styles.modalCard}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={styles.modalIconRing}>
              <svg
                width="26"
                height="26"
                viewBox="0 0 24 24"
                fill="none"
                stroke="#dc2626"
                strokeWidth="2.3"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>

            <h2 id="invalid-url-modal-title" style={styles.modalTitle}>
              Invalid Website URL
            </h2>

            <p style={styles.modalDescription}>
              {invalidUrlReason || "The website URL you entered is invalid or could not be reached. Please check the address and try again."}
            </p>

            <button
              id="close-invalid-url-modal"
              onClick={() => setShowInvalidUrlModal(false)}
              style={styles.modalOkButton}
              autoFocus
            >
              OK
            </button>
          </div>
        </div>
      )}

      {/* POPUP MODAL: STATUTORY REPORT GENERATOR */}
      {showReportModal && report && (
        <div
          id="report-generator-modal-backdrop"
          style={styles.modalBackdrop}
          onClick={() => setShowReportModal(false)}
          role="dialog"
          aria-modal="true"
          aria-labelledby="report-modal-title"
        >
          <div
            id="report-generator-modal-card"
            style={styles.reportModalCard}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div style={styles.reportModalHeader}>
              <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
                <div style={styles.reportModalIconBadge}>
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                    <polyline points="14 2 14 8 20 8" />
                    <line x1="16" y1="13" x2="8" y2="13" />
                    <line x1="16" y1="17" x2="8" y2="17" />
                    <polyline points="10 9 9 9 8 9" />
                  </svg>
                </div>
                <div>
                  <h2 id="report-modal-title" style={styles.reportModalTitle}>
                    DPDP Statutory Audit Report Generator
                  </h2>
                  <p style={styles.reportModalSub}>
                    Generate and download official compliance reports under DPDP Act 2023 & Rules 2025
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowReportModal(false)}
                style={styles.modalCloseBtn}
                title="Close modal"
              >
                ✕
              </button>
            </div>

            {/* Target Summary Strip */}
            <div style={styles.reportModalSummaryStrip}>
              <div style={styles.reportModalSummaryItem}>
                <span style={styles.reportModalSummaryLabel}>Target Website</span>
                <span style={styles.reportModalSummaryVal}>{report.website || websiteUrl}</span>
              </div>
              <div style={styles.reportModalSummaryItem}>
                <span style={styles.reportModalSummaryLabel}>Compliance Score</span>
                <span style={{
                  ...styles.reportModalSummaryVal,
                  color: scoring.score >= 80 ? "#34d399" : scoring.score >= 50 ? "#fbbf24" : "#f87171"
                }}>
                  {scoring.score != null ? `${scoring.score}%` : "N/A"}
                </span>
              </div>
              <div style={styles.reportModalSummaryItem}>
                <span style={styles.reportModalSummaryLabel}>Provisions Evaluated</span>
                <span style={styles.reportModalSummaryVal}>{findings.length} Requirements</span>
              </div>
              <div style={styles.reportModalSummaryItem}>
                <span style={styles.reportModalSummaryLabel}>Regime Stage</span>
                <span style={styles.reportModalSummaryVal}>Rules 2025 ({compliance?.assessment_date || "2027-01-01"})</span>
              </div>
            </div>

            {/* Notification message toast */}
            {downloadNotice && (
              <div style={styles.downloadNoticeToast}>
                <span>✓</span>
                <span>{downloadNotice}</span>
              </div>
            )}

            {/* Format Selection Cards Grid */}
            <div style={styles.reportFormatsGrid}>
              {/* Option 1: Executive PDF / Print Report */}
              <div style={styles.reportFormatCard}>
                <div style={styles.reportFormatTop}>
                  <div style={styles.reportFormatIcon}>📄</div>
                  <span style={styles.reportFormatBadgeGreen}>RECOMMENDED</span>
                </div>
                <h3 style={styles.reportFormatTitle}>Executive PDF Audit Report</h3>
                <p style={styles.reportFormatDesc}>
                  Official publication-ready audit document with statutory seal, executive scorecards, summary distribution, and complete evidence tables.
                </p>
                <button
                  onClick={() => {
                    printPdfReport(report, websiteUrl);
                    setDownloadNotice("Opening print dialog to Save as PDF...");
                    setTimeout(() => setDownloadNotice(""), 3500);
                  }}
                  style={styles.reportDownloadBtnPrimary}
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="6 9 6 2 18 2 18 9" />
                    <path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2" />
                    <rect x="6" y="14" width="12" height="8" />
                  </svg>
                  <span>Download / Print PDF</span>
                </button>
              </div>

              {/* Option 2: CSV Compliance Matrix */}
              <div style={styles.reportFormatCard}>
                <div style={styles.reportFormatTop}>
                  <div style={styles.reportFormatIcon}>📊</div>
                  <span style={styles.reportFormatBadgeBlue}>FOR LEGAL & AUDITORS</span>
                </div>
                <h3 style={styles.reportFormatTitle}>CSV Compliance Matrix</h3>
                <p style={styles.reportFormatDesc}>
                  Structured spreadsheet matrix formatted for Microsoft Excel or Google Sheets. Includes law provisions, sections, reasoning, and discovered evidence.
                </p>
                <button
                  onClick={() => {
                    downloadCsvReport(report, websiteUrl);
                    setDownloadNotice("CSV compliance matrix downloaded successfully!");
                    setTimeout(() => setDownloadNotice(""), 3500);
                  }}
                  style={styles.reportDownloadBtnSecondary}
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>Download CSV (.csv)</span>
                </button>
              </div>

              {/* Option 3: Standalone Offline HTML Report */}
              <div style={styles.reportFormatCard}>
                <div style={styles.reportFormatTop}>
                  <div style={styles.reportFormatIcon}>🌐</div>
                  <span style={styles.reportFormatBadgePurple}>STANDALONE & OFFLINE</span>
                </div>
                <h3 style={styles.reportFormatTitle}>Offline HTML Report</h3>
                <p style={styles.reportFormatDesc}>
                  Zero-dependency interactive HTML document. Can be opened offline in any browser, attached to compliance audits, or emailed to stakeholders.
                </p>
                <button
                  onClick={() => {
                    downloadHtmlReport(report, websiteUrl);
                    setDownloadNotice("Standalone HTML report downloaded!");
                    setTimeout(() => setDownloadNotice(""), 3500);
                  }}
                  style={styles.reportDownloadBtnSecondary}
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>Download HTML (.html)</span>
                </button>
              </div>

              {/* Option 4: Full Audit JSON Telemetry */}
              <div style={styles.reportFormatCard}>
                <div style={styles.reportFormatTop}>
                  <div style={styles.reportFormatIcon}>⚙️</div>
                  <span style={styles.reportFormatBadgeSlate}>RAW TELEMETRY</span>
                </div>
                <h3 style={styles.reportFormatTitle}>Machine-Readable JSON</h3>
                <p style={styles.reportFormatDesc}>
                  Full structured JSON payload including crawler evidence nodes, model evaluations, section scoring, and metadata for GRC tools and SIEM.
                </p>
                <button
                  onClick={() => {
                    downloadJsonReport(report, websiteUrl);
                    setDownloadNotice("Audit JSON telemetry downloaded!");
                    setTimeout(() => setDownloadNotice(""), 3500);
                  }}
                  style={styles.reportDownloadBtnSecondary}
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>Download JSON (.json)</span>
                </button>
              </div>
            </div>

            {/* Modal Bottom Note */}
            <div style={styles.reportModalFooter}>
              <div style={styles.reportModalNoticeText}>
                ⚖ All exports conform to India's DPDP Act, 2023 & DPDP Rules, 2025 statutory assessment guidelines.
              </div>
              <button
                onClick={() => setShowReportModal(false)}
                style={styles.reportModalCloseActionBtn}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div style={styles.container}>
        {/* HEADER */}
        <div style={styles.header}>
          <div style={styles.badgeTop}>
            <span style={styles.badgeTopDot} />
            <span>STATUTORY AI AUDIT ENGINE • DPDP ACT 2023 & RULES 2025</span>
          </div>
          <h1 style={styles.title}>DPDP Compliance Intelligence</h1>
          <p style={styles.subtitle}>
            Autonomous Statutory Evidence Discovery & Regulatory Compliance Screening Engine
          </p>
        </div>

        {/* INPUT CARD */}
        <div style={styles.card}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
            <label style={styles.label}>Target Website to Screen</label>
            <span style={styles.sslNotice}>⚡ Automated Forensic Browser Inspection</span>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (!loading) {
                scanWebsite(websiteUrl);
              }
            }}
            style={styles.inputRow}
          >
            <div style={styles.inputContainer}>
              <span style={styles.inputIcon}>
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#0d9488" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="2" y1="12" x2="22" y2="12" />
                  <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
                </svg>
              </span>
              <input
                type="text"
                value={websiteUrl}
                onChange={(e) => setWebsiteUrl(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !loading) {
                    e.preventDefault();
                    scanWebsite(e.target.value);
                  }
                }}
                placeholder="Enter domain (e.g. flipkart.com, swiggy.com)..."
                style={styles.input}
                disabled={loading}
              />
            </div>
            <button
              type="submit"
              onClick={(e) => {
                e.preventDefault();
                if (!loading) {
                  scanWebsite(websiteUrl);
                }
              }}
              disabled={loading}
              style={{
                ...styles.button,
                ...(loading ? styles.buttonLoading : {}),
                opacity: loading ? 0.9 : 1,
                cursor: loading ? "not-allowed" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "10px",
              }}
            >
              {loading ? (
                <>
                  <span
                    style={{
                      width: "14px",
                      height: "14px",
                      border: "2px solid rgba(255, 255, 255, 0.25)",
                      borderTopColor: "#ffffff",
                      borderRadius: "50%",
                      animation: "spin 0.7s linear infinite",
                      display: "inline-block",
                      flexShrink: 0,
                    }}
                  />
                  <span>Screening Domain...</span>
                </>
              ) : (
                <>
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="#ffffff"
                    strokeWidth="2.4"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" cy="21" x2="16.65" y2="16.65" />
                  </svg>
                  <span>Screen Domain</span>
                </>
              )}
            </button>
          </form>

          {/* QUICK TARGET PRESETS */}
          <div style={styles.presetRow}>
            <span style={styles.presetLabel}>Quick Presets:</span>
            {["flipkart.com", "swiggy.com", "tatadigital.com", "zerodha.com"].map((domain) => (
              <button
                key={domain}
                type="button"
                onClick={() => {
                  setWebsiteUrl(domain);
                  if (error) setError("");
                }}
                disabled={loading}
                style={styles.presetChip}
              >
                {domain}
              </button>
            ))}
          </div>

          {/* CONTINUOUS PIPELINE SCANNER PROGRESS */}
          {loading && (
            <ModernScanProgress
              websiteUrl={activeScanningUrl || websiteUrl}
              currentStepIndex={scanStep}
              isPhaseTwo={isPhaseTwo}
              hasError={false}
              errorMessage=""
            />
          )}

          {error && !loading && (
            <div style={styles.errorBox}>
              <div style={{ display: "flex", alignItems: "center", gap: "8px", fontWeight: "700" }}>
                <span>✕</span>
                <span>Scan Error</span>
              </div>
              <div style={{ marginTop: "4px", fontSize: "13px" }}>{error}</div>
            </div>
          )}
        </div>

        {/* SCAN METADATA & REPORT GENERATOR ACTION */}
        {report && (
          <div style={styles.scanMetaCard}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "14px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                <span style={styles.metaIcon}>🌐</span>
                <span style={styles.metaLabel}>Target Website:</span>
                <span style={styles.metaDomainValue}>
                  {report?.website || websiteUrl.trim()}
                </span>
                <span style={styles.verifiedSSLBadge}>✓ Verified Web Evidence</span>
                {classification && (
                  <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                    <span style={styles.metaLabel}>Sector:</span>
                    <span style={styles.categoryBadge}>
                      {(classification.category || "General").toUpperCase()}
                    </span>
                  </div>
                )}
                <div style={styles.timestampBadge}>
                  Assessed: {compliance?.assessment_date || "2027-01-01"}
                </div>
              </div>

              {/* DOWNLOAD REPORT TRIGGER */}
              <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
                <button
                  id="open-report-generator-btn"
                  onClick={() => setShowReportModal(true)}
                  style={styles.openReportModalBtn}
                  title="Generate and download official compliance report"
                >
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  <span>Download Report</span>
                  <span style={styles.reportModalPillTag}>PDF • CSV • JSON</span>
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ASSESSMENT REPORT */}
        {report && (
          <>
            {/* METRICS ROW */}
            <div style={styles.metricsGrid}>
              <div style={{ ...styles.metricCard, borderTop: `2px solid ${scoring.score >= 80 ? "#0f766e" : scoring.score >= 50 ? "#d97706" : "#e11d48"}` }}>
                <div style={styles.metricTitle}>Statutory Compliance Score</div>
                <div style={{
                  ...styles.metricValue,
                  color: scoring.score >= 80 ? "#0f766e" : scoring.score >= 50 ? "#b45309" : "#be123c",
                  textShadow: `0 0 20px ${scoring.score >= 80 ? "rgba(15, 118, 110, 0.15)" : scoring.score >= 50 ? "rgba(217, 119, 6, 0.15)" : "rgba(225, 29, 72, 0.15)"}`
                }}>
                  {scoring.score != null ? `${scoring.score}%` : "N/A"}
                </div>
                <div style={styles.metricSub}>
                  Assessed among {scoring.total_scoreable ?? 0} scoreable provisions
                </div>
              </div>

              <div style={{ ...styles.metricCard, borderTop: "2px solid #0d9488" }}>
                <div style={styles.metricTitle}>Evidence Coverage Ratio</div>
                <div style={{ ...styles.metricValue, color: "#0d9488", textShadow: "0 0 20px rgba(13, 148, 136, 0.15)" }}>
                  {scoring.evidence_coverage_display ?? (scoring.evidence_coverage != null ? `${scoring.evidence_coverage}%` : "N/A")}
                </div>
                <div style={styles.metricSub}>
                  {scoring.total_scoreable ?? 0} of {scoring.total_currently_applicable ?? 47} applicable requirements verified
                </div>
              </div>

              <div style={{ ...styles.metricCard, borderTop: "2px solid #d4af37" }}>
                <div style={styles.metricTitle}>Applicability Regime</div>
                <div style={{ ...styles.metricValue, color: "#854d0e", fontSize: "24px", textShadow: "0 0 20px rgba(212, 175, 55, 0.15)" }}>
                  Rules 2025 (Phased)
                </div>
                <div style={styles.metricSub}>
                  Simulated post-commencement ({compliance?.assessment_date || "2027-01-01"})
                </div>
              </div>
            </div>

            {/* BREAKDOWN SUMMARY */}
            <div style={styles.card}>
              <h2 style={styles.sectionHeading}>Assessment Summary</h2>
              <p style={{ color: "#64748b", fontSize: "14px", marginTop: "4px" }}>
                {scoring.message}
              </p>

              <div style={styles.breakdownGrid}>
                <div style={{ ...styles.breakdownItem, borderLeft: "3px solid #0f766e", background: "rgba(15, 118, 110, 0.06)", border: "1px solid rgba(15, 118, 110, 0.2)" }}>
                  <div style={{ ...styles.breakdownCount, color: "#0f766e" }}>{scoring.compliant ?? 0}</div>
                  <div style={styles.breakdownLabel}>Fully Compliant</div>
                </div>
                <div style={{ ...styles.breakdownItem, borderLeft: "3px solid #d97706", background: "rgba(217, 119, 6, 0.06)", border: "1px solid rgba(217, 119, 6, 0.2)" }}>
                  <div style={{ ...styles.breakdownCount, color: "#b45309" }}>{scoring.partially_compliant ?? 0}</div>
                  <div style={styles.breakdownLabel}>Partially Compliant</div>
                </div>
                <div style={{ ...styles.breakdownItem, borderLeft: "3px solid #e11d48", background: "rgba(225, 29, 72, 0.06)", border: "1px solid rgba(225, 29, 72, 0.2)" }}>
                  <div style={{ ...styles.breakdownCount, color: "#be123c" }}>{scoring.non_compliant ?? 0}</div>
                  <div style={styles.breakdownLabel}>Non-Compliant</div>
                </div>
                <div style={{ ...styles.breakdownItem, borderLeft: "3px solid #64748b", background: "rgba(100, 116, 139, 0.05)", border: "1px solid rgba(100, 116, 139, 0.18)" }}>
                  <div style={{ ...styles.breakdownCount, color: "#334155" }}>{scoring.insufficient_evidence ?? 0}</div>
                  <div style={styles.breakdownLabel}>Insufficient Evidence</div>
                </div>
              </div>
            </div>

            {/* FINDINGS WITH ACCORDION LIST */}
            <div style={styles.card}>
              <div style={styles.findingsHeader}>
                <div>
                  <h2 style={styles.sectionHeading}>Requirement-by-Requirement Findings</h2>
                  <p style={{ color: "#64748b", fontSize: "13px", marginTop: "4px" }}>
                    Showing {filteredFindings.length} of {findings.length} statutory requirements. Click any provision to review legal scope, reasoning, guidance, and evidence.
                  </p>
                </div>

                {/* EXPAND / COLLAPSE & QUICK EXPORT BUTTONS */}
                <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
                  <button
                    onClick={expandAll}
                    style={styles.actionBtn}
                    title="Expand all provisions"
                  >
                    Expand All
                  </button>
                  <button
                    onClick={collapseAll}
                    style={styles.actionBtn}
                    title="Collapse all provisions"
                  >
                    Collapse All
                  </button>
                  <div style={styles.quickExportGroup}>
                    <button
                      onClick={() => {
                        printPdfReport(report, websiteUrl);
                        setDownloadNotice("Opening print dialog to Save as PDF...");
                        setTimeout(() => setDownloadNotice(""), 3500);
                      }}
                      style={styles.quickExportBtn}
                      title="Print or Save PDF Report"
                    >
                      📄 PDF
                    </button>
                    <button
                      onClick={() => {
                        downloadCsvReport(report, websiteUrl);
                        setDownloadNotice("CSV compliance matrix downloaded successfully!");
                        setTimeout(() => setDownloadNotice(""), 3500);
                      }}
                      style={styles.quickExportBtn}
                      title="Download CSV Compliance Matrix"
                    >
                      📊 CSV
                    </button>
                    <button
                      onClick={() => {
                        downloadJsonReport(report, websiteUrl);
                        setDownloadNotice("Audit JSON telemetry downloaded!");
                        setTimeout(() => setDownloadNotice(""), 3500);
                      }}
                      style={styles.quickExportBtn}
                      title="Download JSON Telemetry"
                    >
                      ⚙️ JSON
                    </button>
                  </div>
                </div>
              </div>

              {/* CONTROLS ROW: TABS + SEARCH */}
              <div style={styles.controlsRow}>
                {/* FILTER TABS */}
                <div style={styles.tabContainer}>
                  <button
                    onClick={() => setFilterStatus("all")}
                    style={filterStatus === "all" ? styles.tabActive : styles.tab}
                  >
                    All ({findings.length})
                  </button>
                  <button
                    onClick={() => setFilterStatus("scoreable")}
                    style={filterStatus === "scoreable" ? styles.tabActive : styles.tab}
                  >
                    Evidenced ({scoring.total_scoreable ?? 0})
                  </button>
                  <button
                    onClick={() => setFilterStatus("compliant")}
                    style={filterStatus === "compliant" ? styles.tabActive : styles.tab}
                  >
                    Compliant ({scoring.compliant ?? 0})
                  </button>
                  <button
                    onClick={() => setFilterStatus("partially_compliant")}
                    style={filterStatus === "partially_compliant" ? styles.tabActive : styles.tab}
                  >
                    Partial ({scoring.partially_compliant ?? 0})
                  </button>
                  <button
                    onClick={() => setFilterStatus("non_compliant")}
                    style={filterStatus === "non_compliant" ? styles.tabActive : styles.tab}
                  >
                    Non-Compliant ({scoring.non_compliant ?? 0})
                  </button>
                  <button
                    onClick={() => setFilterStatus("insufficient_evidence")}
                    style={filterStatus === "insufficient_evidence" ? styles.tabActive : styles.tab}
                  >
                    Unverified ({scoring.insufficient_evidence ?? 0})
                  </button>
                </div>

                {/* SEARCH INPUT */}
                <div style={styles.searchWrapper}>
                  <span style={styles.searchIcon}>🔎</span>
                  <input
                    type="text"
                    placeholder="Search acts, sections, or rules..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    style={styles.searchInput}
                  />
                  {searchTerm && (
                    <button
                      onClick={() => setSearchTerm("")}
                      style={styles.searchClearBtn}
                      title="Clear search"
                    >
                      ×
                    </button>
                  )}
                </div>
              </div>

              {/* ACCORDION LIST */}
              <div style={{ marginTop: "16px" }}>
                {filteredFindings.length === 0 ? (
                  <div style={styles.emptyState}>
                    No statutory requirements match the current filters.
                  </div>
                ) : (
                  filteredFindings.map((finding, idx) => {
                    const itemId = finding.requirement_id || `item-${idx}`;
                    const isExpanded = expandedIds.has(itemId);
                    const badgeStyle = getStatusBadgeStyle(finding.status);
                    const actTitle = getActTitle(finding);
                    const actRef = getActRef(finding);
                    const lawBadge = getActLawBadge(finding);
                    const isRules = lawBadge.includes("Rules");

                    const shortExplanation = getShortActExplanation(finding);
                    const shortReasoning = getShortReasoning(finding);
                    const shortGuidance = getShortGuidance(finding);
                    const cleanEvidence = extractCleanEvidence(finding.evidence);

                    return (
                      <div key={itemId} style={styles.accordionContainer}>
                        {/* ACCORDION ROW: Act Name + Compliant/Not Box ON THE SAME LINE */}
                        <div
                          onClick={() => toggleExpand(itemId)}
                          style={{
                            ...styles.accordionRow,
                            ...(isExpanded ? styles.accordionRowExpanded : {}),
                          }}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(e) => {
                            if (e.key === "Enter" || e.key === " ") {
                              e.preventDefault();
                              toggleExpand(itemId);
                            }
                          }}
                        >
                          {/* Left side: Chevron + Law Tag + Section Ref + Act Name */}
                          <div style={styles.accordionLeft}>
                            <span
                              style={{
                                ...styles.chevron,
                                transform: isExpanded ? "rotate(90deg)" : "rotate(0deg)",
                              }}
                            >
                              ▶
                            </span>
                            <span
                              style={{
                                ...styles.lawBadge,
                                backgroundColor: isRules ? "rgba(212, 175, 55, 0.15)" : "rgba(15, 118, 110, 0.1)",
                                color: isRules ? "#854d0e" : "#0f766e",
                                borderColor: isRules ? "rgba(212, 175, 55, 0.45)" : "rgba(15, 118, 110, 0.35)",
                              }}
                            >
                              {lawBadge}
                            </span>
                            <span style={styles.refBadge}>{actRef}</span>
                            <span style={styles.actTitleText}>{actTitle}</span>
                          </div>

                          {/* Right side: Compliant or Not Box ON THE SAME LINE */}
                          <div style={styles.accordionRight}>
                            <span style={{ ...styles.statusBadge, ...badgeStyle }}>
                              {formatStatusBadgeText(finding.status)}
                            </span>
                          </div>
                        </div>

                        {/* EXPANDED CONTENT: 4 SHORT, EASY TO UNDERSTAND CARDS */}
                        {isExpanded && (
                          <div style={styles.accordionBody}>
                            <div style={styles.scannerGrid}>
                              {/* 1. Act Explanation */}
                              <div style={styles.scannerCard}>
                                <div style={styles.scannerCardHeader}>
                                  <span style={styles.scannerCardIcon}>📜</span>
                                  <div>
                                    <div style={styles.scannerCardTitle}>Act Explanation</div>
                                    <div style={styles.scannerCardSub}>Statutory Legal Mandate</div>
                                  </div>
                                </div>
                                <div style={styles.scannerCardContent}>
                                  {shortExplanation}
                                </div>
                              </div>

                              {/* 2. Semantic Reasoning & Evaluation */}
                              <div style={styles.scannerCard}>
                                <div style={styles.scannerCardHeader}>
                                  <span style={styles.scannerCardIcon}>🧠</span>
                                  <div>
                                    <div style={styles.scannerCardTitle}>Semantic Reasoning &amp; Evaluation</div>
                                    <div style={styles.scannerCardSub}>Scanner Assessment</div>
                                  </div>
                                </div>
                                <div style={styles.scannerCardContent}>
                                  {shortReasoning}
                                </div>
                              </div>

                              {/* 3. Compliance Guidance */}
                              <div style={styles.scannerCard}>
                                <div style={styles.scannerCardHeader}>
                                  <span style={styles.scannerCardIcon}>💡</span>
                                  <div>
                                    <div style={styles.scannerCardTitle}>Compliance Guidance</div>
                                    <div style={styles.scannerCardSub}>Actionable Remediation</div>
                                  </div>
                                </div>
                                <div style={styles.scannerCardContent}>
                                  {shortGuidance}
                                </div>
                              </div>

                              {/* 4. Evidence */}
                              <div style={styles.scannerCard}>
                                <div style={styles.scannerCardHeader}>
                                  <span style={styles.scannerCardIcon}>🔍</span>
                                  <div>
                                    <div style={styles.scannerCardTitle}>Discovered Evidence</div>
                                    <div style={styles.scannerCardSub}>Observable Website Signals</div>
                                  </div>
                                </div>
                                <div style={styles.scannerCardContent}>
                                  {renderCleanEvidenceView(cleanEvidence)}
                                </div>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })
                )}
              </div>
            </div>

            {/* LEGAL DISCLAIMER */}
            <div style={styles.disclaimerCard}>
              <strong>Statutory Compliance Screening Disclaimer:</strong>
              <p style={{ marginTop: "6px", lineHeight: "1.5" }}>
                This automated compliance assessment is an evidence-based technical screening of publicly observable
                website elements under India's Digital Personal Data Protection Act, 2023 and DPDP Rules, 2025.
                Public website evidence cannot verify internal organizational controls, confidential vendor contracts,
                or backend security configurations. This screening does not constitute legal counsel or a definitive
                statutory certification.
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    backgroundColor: "transparent",
    padding: "48px 24px",
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    color: "#0f172a",
  },
  container: {
    maxWidth: "1180px",
    margin: "0 auto",
  },
  header: {
    textAlign: "center",
    marginBottom: "40px",
  },
  badgeTop: {
    display: "inline-flex",
    alignItems: "center",
    gap: "8px",
    backgroundColor: "rgba(15, 118, 110, 0.08)",
    color: "#0f766e",
    padding: "6px 18px",
    borderRadius: "24px",
    fontSize: "11px",
    fontWeight: "800",
    letterSpacing: "0.08em",
    border: "1px solid rgba(212, 175, 55, 0.45)",
    marginBottom: "16px",
    boxShadow: "0 2px 12px rgba(212, 175, 55, 0.15), inset 0 1px 0 rgba(255, 255, 255, 0.8)",
  },
  badgeTopDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    backgroundColor: "#d4af37",
    boxShadow: "0 0 10px #d4af37, 0 0 16px rgba(212, 175, 55, 0.5)",
    animation: "goldGlowPulse 2s infinite",
  },
  title: {
    fontSize: "42px",
    fontWeight: "800",
    background: "linear-gradient(180deg, #0f172a 20%, #1e293b 60%, #0f766e 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
    margin: "0 0 12px 0",
    letterSpacing: "-0.035em",
    lineHeight: "1.15",
  },
  subtitle: {
    fontSize: "15px",
    color: "#475569",
    margin: 0,
    maxWidth: "680px",
    marginLeft: "auto",
    marginRight: "auto",
    lineHeight: "1.6",
    letterSpacing: "-0.01em",
  },
  card: {
    backgroundColor: "rgba(255, 255, 255, 0.94)",
    backdropFilter: "blur(24px)",
    WebkitBackdropFilter: "blur(24px)",
    borderRadius: "20px",
    padding: "30px 34px",
    boxShadow: "0 20px 40px -15px rgba(15, 23, 42, 0.07), 0 0 0 1px rgba(212, 175, 55, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.9)",
    marginBottom: "24px",
    border: "1px solid rgba(212, 175, 55, 0.32)",
  },
  label: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#0f172a",
    letterSpacing: "0.06em",
    textTransform: "uppercase",
  },
  sslNotice: {
    fontSize: "11px",
    color: "#0f766e",
    fontWeight: "600",
    letterSpacing: "0.03em",
  },
  inputRow: {
    display: "flex",
    gap: "12px",
  },
  inputContainer: {
    position: "relative",
    flex: 1,
    display: "flex",
    alignItems: "center",
  },
  inputIcon: {
    position: "absolute",
    left: "16px",
    display: "flex",
    alignItems: "center",
    pointerEvents: "none",
  },
  input: {
    width: "100%",
    padding: "15px 20px 15px 46px",
    fontSize: "15px",
    borderRadius: "14px",
    border: "1.5px solid rgba(212, 175, 55, 0.38)",
    backgroundColor: "#ffffff",
    color: "#0f172a",
    outline: "none",
    boxSizing: "border-box",
    transition: "border-color 0.2s, box-shadow 0.2s",
    fontFamily: "'Inter', sans-serif",
    boxShadow: "0 2px 6px rgba(15, 23, 42, 0.04), inset 0 1px 2px rgba(0, 0, 0, 0.02)",
  },
  button: {
    padding: "15px 32px",
    fontSize: "14px",
    fontWeight: "700",
    color: "#ffffff",
    background: "linear-gradient(135deg, #0f766e 0%, #115e59 50%, #d4af37 100%)",
    border: "1px solid rgba(254, 240, 138, 0.5)",
    borderRadius: "14px",
    cursor: "pointer",
    boxShadow: "0 6px 20px rgba(15, 118, 110, 0.28), 0 2px 8px rgba(212, 175, 55, 0.25)",
    transition: "all 0.2s cubic-bezier(0.16, 1, 0.3, 1)",
    whiteSpace: "nowrap",
  },
  buttonLoading: {
    background: "linear-gradient(135deg, #0f766e 0%, #334155 100%)",
    border: "1px solid rgba(212, 175, 55, 0.4)",
    boxShadow: "none",
  },
  presetRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginTop: "14px",
    flexWrap: "wrap",
  },
  presetLabel: {
    fontSize: "11px",
    color: "#64748b",
    fontWeight: "600",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  presetChip: {
    backgroundColor: "#ffffff",
    border: "1px solid rgba(212, 175, 55, 0.3)",
    borderRadius: "6px",
    padding: "4px 10px",
    fontSize: "12px",
    color: "#334155",
    cursor: "pointer",
    transition: "all 0.15s ease",
    fontFamily: "'JetBrains Mono', monospace",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.04)",
  },
  stageBox: {
    marginTop: "16px",
    padding: "12px 16px",
    backgroundColor: "rgba(15, 118, 110, 0.08)",
    borderRadius: "8px",
    color: "#0f766e",
    fontSize: "14px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    border: "1px solid rgba(212, 175, 55, 0.35)",
  },
  spinner: {
    width: "16px",
    height: "16px",
    border: "2px solid rgba(212, 175, 55, 0.3)",
    borderTopColor: "#b45309",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    flexShrink: 0,
    display: "inline-block",
    boxSizing: "border-box",
  },
  errorBox: {
    marginTop: "16px",
    padding: "16px 20px",
    backgroundColor: "rgba(225, 29, 72, 0.08)",
    borderRadius: "12px",
    color: "#be123c",
    fontSize: "14px",
    border: "1px solid rgba(225, 29, 72, 0.3)",
  },
  scanMetaCard: {
    backgroundColor: "rgba(255, 255, 255, 0.94)",
    backdropFilter: "blur(20px)",
    borderRadius: "16px",
    padding: "18px 26px",
    fontSize: "13px",
    color: "#334155",
    marginBottom: "24px",
    border: "1px solid rgba(212, 175, 55, 0.32)",
    boxShadow: "0 15px 35px -5px rgba(15, 23, 42, 0.06), 0 0 0 1px rgba(212, 175, 55, 0.15)",
  },
  openReportModalBtn: {
    display: "inline-flex",
    alignItems: "center",
    gap: "8px",
    background: "linear-gradient(135deg, #0f766e 0%, #115e59 50%, #d4af37 100%)",
    color: "#ffffff",
    border: "1px solid rgba(254, 240, 138, 0.5)",
    padding: "9px 18px",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "700",
    cursor: "pointer",
    boxShadow: "0 4px 16px rgba(15, 118, 110, 0.25), 0 2px 6px rgba(212, 175, 55, 0.2)",
    transition: "all 0.15s ease",
  },
  reportModalPillTag: {
    fontSize: "10px",
    fontWeight: "800",
    backgroundColor: "rgba(254, 240, 138, 0.35)",
    color: "#854d0e",
    padding: "2px 7px",
    borderRadius: "4px",
    letterSpacing: "0.04em",
    border: "1px solid rgba(212, 175, 55, 0.4)",
  },
  metaIcon: {
    fontSize: "16px",
  },
  metaLabel: {
    fontSize: "12px",
    color: "#64748b",
    fontWeight: "600",
    textTransform: "uppercase",
    letterSpacing: "0.04em",
  },
  metaDomainValue: {
    fontWeight: "700",
    color: "#0f766e",
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: "14px",
  },
  verifiedSSLBadge: {
    fontSize: "11px",
    fontWeight: "700",
    backgroundColor: "rgba(13, 148, 136, 0.1)",
    color: "#0f766e",
    padding: "3px 10px",
    borderRadius: "20px",
    border: "1px solid rgba(13, 148, 136, 0.3)",
    letterSpacing: "0.02em",
  },
  categoryBadge: {
    backgroundColor: "rgba(212, 175, 55, 0.15)",
    color: "#854d0e",
    padding: "4px 12px",
    borderRadius: "6px",
    fontWeight: "700",
    fontSize: "12px",
    border: "1px solid rgba(212, 175, 55, 0.4)",
  },
  timestampBadge: {
    fontSize: "11px",
    color: "#475569",
    fontFamily: "'JetBrains Mono', monospace",
    backgroundColor: "#f1f5f9",
    padding: "4px 10px",
    borderRadius: "6px",
    border: "1px solid #e2e8f0",
  },
  code: {
    fontFamily: "'JetBrains Mono', monospace",
    backgroundColor: "#f8fafc",
    padding: "3px 8px",
    borderRadius: "6px",
    color: "#0f766e",
    border: "1px solid rgba(212, 175, 55, 0.28)",
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "18px",
    marginBottom: "24px",
  },
  metricCard: {
    backgroundColor: "#ffffff",
    backdropFilter: "blur(20px)",
    WebkitBackdropFilter: "blur(20px)",
    borderRadius: "18px",
    padding: "26px 30px",
    boxShadow: "0 10px 25px -5px rgba(15, 23, 42, 0.05), 0 0 0 1px rgba(212, 175, 55, 0.18)",
    border: "1px solid rgba(212, 175, 55, 0.28)",
  },
  metricTitle: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  },
  metricValue: {
    fontSize: "40px",
    fontWeight: "800",
    margin: "12px 0 6px 0",
    letterSpacing: "-0.03em",
  },
  metricSub: {
    fontSize: "13px",
    color: "#64748b",
    lineHeight: "1.4",
  },
  sectionHeading: {
    fontSize: "20px",
    fontWeight: "700",
    color: "#0f172a",
    margin: 0,
    letterSpacing: "-0.01em",
  },
  breakdownGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
    gap: "14px",
    marginTop: "20px",
  },
  breakdownItem: {
    padding: "18px 22px",
    borderRadius: "14px",
    border: "1px solid rgba(212, 175, 55, 0.2)",
    backdropFilter: "blur(12px)",
  },
  breakdownCount: {
    fontSize: "30px",
    fontWeight: "800",
    letterSpacing: "-0.02em",
  },
  breakdownLabel: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#64748b",
    marginTop: "4px",
  },
  findingsHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "12px",
    marginBottom: "20px",
  },
  controlsRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "12px",
    paddingBottom: "20px",
    borderBottom: "1px solid #e2e8f0",
  },
  actionBtn: {
    padding: "8px 16px",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "8px",
    border: "1px solid rgba(212, 175, 55, 0.3)",
    backgroundColor: "#ffffff",
    color: "#334155",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },
  quickExportGroup: {
    display: "flex",
    alignItems: "center",
    gap: "6px",
    marginLeft: "4px",
    borderLeft: "1px solid rgba(212, 175, 55, 0.25)",
    paddingLeft: "8px",
  },
  quickExportBtn: {
    padding: "8px 12px",
    fontSize: "11px",
    fontWeight: "700",
    borderRadius: "8px",
    border: "1px solid rgba(212, 175, 55, 0.35)",
    backgroundColor: "rgba(212, 175, 55, 0.1)",
    color: "#854d0e",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    transition: "all 0.15s ease",
  },
  tabContainer: {
    display: "flex",
    gap: "6px",
    flexWrap: "wrap",
  },
  tab: {
    padding: "8px 15px",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "8px",
    border: "1px solid #e2e8f0",
    backgroundColor: "#ffffff",
    color: "#64748b",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },
  tabActive: {
    padding: "8px 15px",
    fontSize: "12px",
    fontWeight: "700",
    borderRadius: "8px",
    border: "1px solid #0f766e",
    backgroundColor: "rgba(15, 118, 110, 0.1)",
    color: "#0f766e",
    cursor: "pointer",
    boxShadow: "0 2px 8px rgba(15, 118, 110, 0.12)",
  },
  searchWrapper: {
    display: "flex",
    alignItems: "center",
    position: "relative",
    minWidth: "270px",
  },
  searchIcon: {
    position: "absolute",
    left: "12px",
    fontSize: "13px",
    pointerEvents: "none",
    color: "#64748b",
  },
  searchInput: {
    padding: "10px 28px 10px 34px",
    fontSize: "13px",
    borderRadius: "10px",
    border: "1px solid rgba(212, 175, 55, 0.35)",
    outline: "none",
    width: "100%",
    backgroundColor: "#ffffff",
    color: "#0f172a",
    transition: "border-color 0.15s",
  },
  searchClearBtn: {
    position: "absolute",
    right: "8px",
    background: "transparent",
    border: "none",
    color: "#64748b",
    cursor: "pointer",
    fontSize: "16px",
    lineHeight: "1",
    padding: "2px",
  },
  emptyState: {
    textAlign: "center",
    padding: "36px 20px",
    color: "#64748b",
    fontSize: "14px",
    backgroundColor: "#ffffff",
    borderRadius: "12px",
    border: "1px dashed rgba(212, 175, 55, 0.3)",
  },
  accordionContainer: {
    marginBottom: "12px",
  },
  accordionRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "16px 22px",
    backgroundColor: "#ffffff",
    backdropFilter: "blur(16px)",
    border: "1px solid rgba(212, 175, 55, 0.25)",
    borderRadius: "14px",
    cursor: "pointer",
    transition: "all 0.15s ease",
    userSelect: "none",
    boxShadow: "0 2px 6px rgba(15, 23, 42, 0.04)",
  },
  accordionRowExpanded: {
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
    marginBottom: 0,
    backgroundColor: "rgba(240, 253, 250, 0.95)",
    borderColor: "rgba(15, 118, 110, 0.5)",
    boxShadow: "0 4px 14px rgba(15, 118, 110, 0.08)",
  },
  accordionLeft: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flex: 1,
    minWidth: 0,
    marginRight: "16px",
    flexWrap: "wrap",
  },
  accordionRight: {
    display: "flex",
    alignItems: "center",
    flexShrink: 0,
  },
  chevron: {
    fontSize: "10px",
    color: "#b45309",
    transition: "transform 0.15s ease",
    display: "inline-block",
    width: "12px",
    textAlign: "center",
  },
  lawBadge: {
    fontSize: "11px",
    fontWeight: "700",
    padding: "3px 9px",
    borderRadius: "6px",
    border: "1px solid",
    letterSpacing: "0.02em",
    whiteSpace: "nowrap",
  },
  refBadge: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#475569",
    backgroundColor: "#f1f5f9",
    padding: "3px 9px",
    borderRadius: "6px",
    border: "1px solid #e2e8f0",
    whiteSpace: "nowrap",
    fontFamily: "'JetBrains Mono', monospace",
  },
  actTitleText: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#0f172a",
    lineHeight: "1.4",
  },
  statusBadge: {
    padding: "5px 12px",
    borderRadius: "8px",
    fontSize: "12px",
    fontWeight: "700",
    whiteSpace: "nowrap",
    letterSpacing: "0.02em",
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
  },
  accordionBody: {
    backgroundColor: "#ffffff",
    border: "1px solid rgba(15, 118, 110, 0.4)",
    borderTop: "none",
    borderBottomLeftRadius: "14px",
    borderBottomRightRadius: "14px",
    padding: "22px",
    boxShadow: "inset 0 2px 6px rgba(0, 0, 0, 0.02)",
  },
  scannerGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "14px",
  },
  scannerCard: {
    backgroundColor: "#f8fafc",
    borderRadius: "12px",
    border: "1px solid #e2e8f0",
    padding: "18px 20px",
    display: "flex",
    flexDirection: "column",
    boxShadow: "0 1px 3px rgba(0, 0, 0, 0.02)",
  },
  scannerCardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "10px",
    paddingBottom: "8px",
    borderBottom: "1px solid #e2e8f0",
  },
  scannerCardIcon: {
    fontSize: "16px",
  },
  scannerCardTitle: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#0f172a",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  scannerCardSub: {
    fontSize: "10px",
    color: "#b45309",
    fontWeight: "600",
  },
  scannerCardContent: {
    fontSize: "13px",
    color: "#334155",
    lineHeight: "1.6",
    flex: 1,
  },
  evidenceEmptyBox: {
    fontSize: "12px",
    color: "#64748b",
    fontStyle: "italic",
    padding: "4px 0",
  },
  evidenceElementRow: {
    backgroundColor: "rgba(15, 118, 110, 0.06)",
    padding: "10px 14px",
    borderRadius: "10px",
    borderLeft: "3px solid #0f766e",
    border: "1px solid rgba(15, 118, 110, 0.2)",
  },
  evidenceElementName: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#0f766e",
  },
  evidenceSourceTag: {
    fontSize: "10px",
    fontWeight: "600",
    backgroundColor: "#ffffff",
    color: "#475569",
    padding: "2px 6px",
    borderRadius: "4px",
    border: "1px solid #e2e8f0",
  },
  evidenceQuoteText: {
    fontSize: "12px",
    color: "#475569",
    marginTop: "4px",
    fontStyle: "italic",
    lineHeight: "1.45",
    wordBreak: "break-word",
  },
  disclaimerCard: {
    backgroundColor: "rgba(212, 175, 55, 0.08)",
    border: "1px solid rgba(212, 175, 55, 0.35)",
    borderRadius: "16px",
    padding: "20px 24px",
    fontSize: "12px",
    color: "#854d0e",
    marginBottom: "32px",
    boxShadow: "0 4px 15px rgba(212, 175, 55, 0.08)",
  },
  modalBackdrop: {
    position: "fixed",
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: "rgba(15, 23, 42, 0.45)",
    backdropFilter: "blur(8px)",
    WebkitBackdropFilter: "blur(8px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 99999,
    padding: "16px",
    animation: "fadeIn 0.18s ease-out",
  },
  modalCard: {
    backgroundColor: "#ffffff",
    borderRadius: "20px",
    maxWidth: "460px",
    width: "100%",
    boxShadow: "0 30px 60px -12px rgba(15, 23, 42, 0.2), 0 0 0 1px rgba(212, 175, 55, 0.25)",
    padding: "32px 28px",
    textAlign: "center",
    animation: "modalSlideUp 0.22s cubic-bezier(0.16, 1, 0.3, 1)",
    boxSizing: "border-box",
    border: "1px solid rgba(212, 175, 55, 0.35)",
  },
  modalIconRing: {
    width: "56px",
    height: "56px",
    borderRadius: "50%",
    backgroundColor: "rgba(225, 29, 72, 0.1)",
    border: "6px solid rgba(225, 29, 72, 0.06)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    margin: "0 auto 16px auto",
  },
  modalTitle: {
    fontSize: "20px",
    fontWeight: "700",
    color: "#0f172a",
    margin: "0 0 8px 0",
    letterSpacing: "-0.01em",
  },
  modalDescription: {
    fontSize: "14px",
    color: "#475569",
    lineHeight: "1.55",
    margin: "0 0 22px 0",
    wordBreak: "break-word",
  },
  modalOkButton: {
    background: "linear-gradient(135deg, #0f766e 0%, #115e59 50%, #d4af37 100%)",
    color: "#ffffff",
    border: "1px solid rgba(254, 240, 138, 0.4)",
    borderRadius: "12px",
    padding: "13px 24px",
    fontSize: "14px",
    fontWeight: "700",
    cursor: "pointer",
    width: "100%",
    transition: "opacity 0.15s ease",
    boxShadow: "0 4px 16px rgba(15, 118, 110, 0.25)",
  },
  reportModalCard: {
    backgroundColor: "#ffffff",
    borderRadius: "22px",
    maxWidth: "760px",
    width: "100%",
    boxShadow: "0 35px 70px -15px rgba(15, 23, 42, 0.2), 0 0 0 1px rgba(212, 175, 55, 0.25)",
    padding: "32px 36px",
    animation: "modalSlideUp 0.22s cubic-bezier(0.16, 1, 0.3, 1)",
    boxSizing: "border-box",
    border: "1px solid rgba(212, 175, 55, 0.35)",
    maxHeight: "90vh",
    overflowY: "auto",
  },
  reportModalHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "flex-start",
    marginBottom: "20px",
    gap: "16px",
  },
  reportModalIconBadge: {
    width: "44px",
    height: "44px",
    borderRadius: "12px",
    backgroundColor: "rgba(15, 118, 110, 0.1)",
    border: "1px solid rgba(212, 175, 55, 0.4)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    flexShrink: 0,
    boxShadow: "0 0 16px rgba(212, 175, 55, 0.15)",
  },
  reportModalTitle: {
    fontSize: "20px",
    fontWeight: "800",
    color: "#0f172a",
    margin: "0 0 4px 0",
    letterSpacing: "-0.02em",
  },
  reportModalSub: {
    fontSize: "13px",
    color: "#64748b",
    margin: 0,
    lineHeight: "1.4",
  },
  modalCloseBtn: {
    background: "#f1f5f9",
    border: "1px solid #e2e8f0",
    color: "#64748b",
    borderRadius: "8px",
    width: "32px",
    height: "32px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    cursor: "pointer",
    fontSize: "14px",
    transition: "all 0.15s ease",
  },
  reportModalSummaryStrip: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(140px, 1fr))",
    gap: "10px",
    backgroundColor: "#f8fafc",
    border: "1px solid rgba(212, 175, 55, 0.25)",
    borderRadius: "12px",
    padding: "12px 18px",
    marginBottom: "22px",
  },
  reportModalSummaryItem: {
    display: "flex",
    flexDirection: "column",
    gap: "2px",
  },
  reportModalSummaryLabel: {
    fontSize: "10px",
    fontWeight: "700",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.06em",
  },
  reportModalSummaryVal: {
    fontSize: "13px",
    fontWeight: "700",
    color: "#0f172a",
    fontFamily: "'JetBrains Mono', monospace",
  },
  downloadNoticeToast: {
    backgroundColor: "rgba(15, 118, 110, 0.1)",
    border: "1px solid rgba(15, 118, 110, 0.3)",
    color: "#0f766e",
    padding: "10px 16px",
    borderRadius: "10px",
    fontSize: "13px",
    fontWeight: "600",
    marginBottom: "18px",
    display: "flex",
    alignItems: "center",
    gap: "8px",
  },
  reportFormatsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "16px",
    marginBottom: "24px",
  },
  reportFormatCard: {
    backgroundColor: "#ffffff",
    border: "1px solid rgba(212, 175, 55, 0.25)",
    borderRadius: "16px",
    padding: "20px 22px",
    display: "flex",
    flexDirection: "column",
    transition: "border-color 0.2s, box-shadow 0.2s",
    boxShadow: "0 4px 12px rgba(15, 23, 42, 0.04)",
  },
  reportFormatTop: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "10px",
  },
  reportFormatIcon: {
    fontSize: "24px",
  },
  reportFormatBadgeGreen: {
    fontSize: "10px",
    fontWeight: "800",
    backgroundColor: "rgba(13, 148, 136, 0.12)",
    color: "#0f766e",
    padding: "3px 8px",
    borderRadius: "6px",
    border: "1px solid rgba(13, 148, 136, 0.35)",
    letterSpacing: "0.05em",
  },
  reportFormatBadgeBlue: {
    fontSize: "10px",
    fontWeight: "800",
    backgroundColor: "rgba(212, 175, 55, 0.15)",
    color: "#854d0e",
    padding: "3px 8px",
    borderRadius: "6px",
    border: "1px solid rgba(212, 175, 55, 0.4)",
    letterSpacing: "0.05em",
  },
  reportFormatBadgePurple: {
    fontSize: "10px",
    fontWeight: "800",
    backgroundColor: "rgba(15, 118, 110, 0.12)",
    color: "#0f766e",
    padding: "3px 8px",
    borderRadius: "6px",
    border: "1px solid rgba(15, 118, 110, 0.3)",
    letterSpacing: "0.05em",
  },
  reportFormatBadgeSlate: {
    fontSize: "10px",
    fontWeight: "800",
    backgroundColor: "rgba(100, 116, 139, 0.1)",
    color: "#475569",
    padding: "3px 8px",
    borderRadius: "6px",
    border: "1px solid rgba(100, 116, 139, 0.25)",
    letterSpacing: "0.05em",
  },
  reportFormatTitle: {
    fontSize: "16px",
    fontWeight: "700",
    color: "#0f172a",
    margin: "0 0 6px 0",
  },
  reportFormatDesc: {
    fontSize: "12px",
    color: "#475569",
    margin: "0 0 16px 0",
    lineHeight: "1.5",
    flex: 1,
  },
  reportDownloadBtnPrimary: {
    background: "linear-gradient(135deg, #0f766e 0%, #115e59 50%, #d4af37 100%)",
    color: "#ffffff",
    border: "1px solid rgba(254, 240, 138, 0.5)",
    borderRadius: "10px",
    padding: "11px 18px",
    fontSize: "13px",
    fontWeight: "700",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    boxShadow: "0 4px 16px rgba(15, 118, 110, 0.25), 0 2px 6px rgba(212, 175, 55, 0.2)",
    transition: "all 0.15s ease",
  },
  reportDownloadBtnSecondary: {
    backgroundColor: "#f8fafc",
    color: "#0f172a",
    border: "1px solid rgba(212, 175, 55, 0.28)",
    borderRadius: "10px",
    padding: "11px 18px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
    transition: "all 0.15s ease",
  },
  reportModalFooter: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    borderTop: "1px solid #e2e8f0",
    paddingTop: "18px",
    gap: "14px",
    flexWrap: "wrap",
  },
  reportModalNoticeText: {
    fontSize: "11px",
    color: "#64748b",
    lineHeight: "1.4",
    flex: 1,
  },
  reportModalCloseActionBtn: {
    backgroundColor: "#f1f5f9",
    color: "#334155",
    border: "1px solid #cbd5e1",
    borderRadius: "8px",
    padding: "8px 18px",
    fontSize: "13px",
    fontWeight: "600",
    cursor: "pointer",
  },
};

export default App;