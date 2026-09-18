import React, { useState } from "react";
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

const CRAWLER_API = "http://127.0.0.1:8080";
const BACKEND_API = "http://127.0.0.1:8081";

function getStatusBadgeStyle(status) {
  switch (status) {
    case "compliant":
      return { background: "#dcfce7", color: "#15803d", border: "1px solid #86efac" };
    case "partially_compliant":
      return { background: "#fef3c7", color: "#b45309", border: "1px solid #fde68a" };
    case "non_compliant":
      return { background: "#fee2e2", color: "#b91c1c", border: "1px solid #fca5a5" };
    case "insufficient_evidence":
      return { background: "#f1f5f9", color: "#475569", border: "1px solid #cbd5e1" };
    case "future_requirement":
      return { background: "#f3e8ff", color: "#7e22ce", border: "1px solid #d8b4fe" };
    case "not_applicable":
      return { background: "#f3f4f6", color: "#6b7280", border: "1px solid #e5e7eb" };
    default:
      return { background: "#f3f4f6", color: "#374151", border: "1px solid #e5e7eb" };
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

function App() {
  const [websiteUrl, setWebsiteUrl] = useState("");
  const [scanId, setScanId] = useState("");
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("");
  const [error, setError] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [expandedIds, setExpandedIds] = useState(new Set());

  async function scanWebsite(targetUrl) {
    const inputVal = (targetUrl || websiteUrl).trim();
    if (!inputVal) {
      setError("Please enter a valid website URL or MongoDB Scan ID.");
      return;
    }

    setLoading(true);
    setError("");
    setReport(null);
    setScanId("");
    setFilterStatus("all");
    setSearchTerm("");

    try {
      let targetScanId = "";

      if (inputVal.startsWith("http://") || inputVal.startsWith("https://")) {
        // STEP 1: Crawl website
        setStage("Crawling website & extracting structured evidence (HTML, UI, PDFs)...");

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

        targetScanId = crawlData.scan_id;
      } else {
        // Direct scan ID provided
        targetScanId = inputVal;
      }

      if (!targetScanId || targetScanId === "null" || targetScanId === "undefined") {
        throw new Error("Invalid Scan ID. Please enter a valid website URL or MongoDB Scan ID.");
      }

      setScanId(targetScanId);

      // STEP 2: Analyze DPDP compliance
      setStage("Running website classification, deterministic evidence mapping, and Gemini semantic evaluation...");

      const analysisResponse = await fetch(
        `${BACKEND_API}/api/analyze/${encodeURIComponent(
          targetScanId
        )}?assessment_date=2027-01-01`
      );

      const analysisData = await analysisResponse.json();

      if (!analysisResponse.ok) {
        throw new Error(analysisData.detail || "Compliance analysis failed.");
      }

      setReport(analysisData);
      setStage("");

      // Automatically open the first finding for an immediate real-scanner preview
      const initialFindings = analysisData?.compliance?.findings || [];
      if (initialFindings.length > 0) {
        setExpandedIds(new Set([initialFindings[0].requirement_id || "item-0"]));
      }
    } catch (err) {
      console.error(err);
      setError(err.message || "An error occurred during scanning.");
      setStage("");
    } finally {
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
      `}</style>
      <div style={styles.container}>
        {/* HEADER */}
        <div style={styles.header}>
          <h1 style={styles.title}>DPDP ACT Compliance Tool</h1>
          <p style={styles.subtitle}>
            AI-Assisted, Evidence-Driven DPDP Act (2023) & Rules (2025) Compliance Screening System
          </p>
        </div>

        {/* INPUT CARD */}
        <div style={styles.card}>
          <label style={styles.label}>Enter Website to Screen</label>
          <div style={styles.inputRow}>
            <input
              type="text"
              value={websiteUrl}
              onChange={(e) => setWebsiteUrl(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !loading) {
                  scanWebsite();
                }
              }}
              placeholder="e.g. https://skcet.ac.in/ or https://www.flipkart.com/"
              style={styles.input}
              disabled={loading}
            />
            <button
              onClick={() => scanWebsite()}
              disabled={loading}
              style={{
                ...styles.button,
                opacity: loading ? 0.7 : 1,
                cursor: loading ? "not-allowed" : "pointer",
                display: "inline-flex",
                alignItems: "center",
                justifyContent: "center",
                gap: "8px",
              }}
            >
              {loading && (
                <span
                  style={{
                    width: "14px",
                    height: "14px",
                    border: "2px solid rgba(255, 255, 255, 0.3)",
                    borderTopColor: "#ffffff",
                    borderRadius: "50%",
                    animation: "spin 0.8s linear infinite",
                    display: "inline-block",
                    flexShrink: 0,
                    boxSizing: "border-box",
                  }}
                />
              )}
              <span>{loading ? "Working..." : "Scan Website"}</span>
            </button>
          </div>

          {/* PROGRESS OR ERROR */}
          {loading && stage && (
            <div style={styles.stageBox}>
              <div style={styles.spinner} />
              <span>{stage}</span>
            </div>
          )}

          {error && (
            <div style={styles.errorBox}>
              <strong>Scan Error:</strong> {error}
            </div>
          )}
        </div>

        {/* SCAN METADATA */}
        {scanId && (
          <div style={styles.scanMetaCard}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <div>
                <strong>MongoDB Scan ID:</strong> <code style={styles.code}>{scanId}</code>
              </div>
              {classification && (
                <div>
                  <strong>Category:</strong>{" "}
                  <span style={styles.categoryBadge}>
                    {(classification.category || "General").toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ASSESSMENT REPORT */}
        {report && (
          <>
            {/* METRICS ROW */}
            <div style={styles.metricsGrid}>
              <div style={styles.metricCard}>
                <div style={styles.metricTitle}>Compliance Score</div>
                <div style={{ ...styles.metricValue, color: "#16a34a" }}>
                  {scoring.score != null ? `${scoring.score}%` : "N/A"}
                </div>
                <div style={styles.metricSub}>
                  Assessed among {scoring.total_scoreable ?? 0} scoreable requirements
                </div>
              </div>

              <div style={styles.metricCard}>
                <div style={styles.metricTitle}>Evidence Coverage</div>
                <div style={{ ...styles.metricValue, color: "#2563eb" }}>
                  {scoring.evidence_coverage_display ?? (scoring.evidence_coverage != null ? `${scoring.evidence_coverage}%` : "N/A")}
                </div>
                <div style={styles.metricSub}>
                  {scoring.total_scoreable ?? 0} of {scoring.total_currently_applicable ?? 47} applicable requirements verified
                </div>
              </div>

              <div style={styles.metricCard}>
                <div style={styles.metricTitle}>Applicability Timeline</div>
                <div style={{ ...styles.metricValue, color: "#475569", fontSize: "20px" }}>
                  {compliance?.assessment_date || "2027-01-01"}
                </div>
                <div style={styles.metricSub}>
                  Simulated post-commencement (Rules 2025 phased timeline)
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
                <div style={{ ...styles.breakdownItem, borderLeft: "4px solid #10b981" }}>
                  <div style={styles.breakdownCount}>{scoring.compliant ?? 0}</div>
                  <div style={styles.breakdownLabel}>Fully Compliant</div>
                </div>
                <div style={{ ...styles.breakdownItem, borderLeft: "4px solid #f59e0b" }}>
                  <div style={styles.breakdownCount}>{scoring.partially_compliant ?? 0}</div>
                  <div style={styles.breakdownLabel}>Partially Compliant</div>
                </div>
                <div style={{ ...styles.breakdownItem, borderLeft: "4px solid #ef4444" }}>
                  <div style={styles.breakdownCount}>{scoring.non_compliant ?? 0}</div>
                  <div style={styles.breakdownLabel}>Non-Compliant</div>
                </div>
                <div style={{ ...styles.breakdownItem, borderLeft: "4px solid #64748b" }}>
                  <div style={styles.breakdownCount}>{scoring.insufficient_evidence ?? 0}</div>
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

                {/* EXPAND / COLLAPSE ALL BUTTONS */}
                <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
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
                                backgroundColor: isRules ? "#f5f3ff" : "#eff6ff",
                                color: isRules ? "#6d28d9" : "#1d4ed8",
                                borderColor: isRules ? "#ddd6fe" : "#bfdbfe",
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
    backgroundColor: "#f8fafc",
    padding: "36px 20px",
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    color: "#0f172a",
  },
  container: {
    maxWidth: "1160px",
    margin: "0 auto",
  },
  header: {
    textAlign: "center",
    marginBottom: "32px",
  },

  title: {
    fontSize: "36px",
    fontWeight: "800",
    color: "#0f172a",
    margin: "0 0 8px 0",
    letterSpacing: "-0.02em",
  },
  subtitle: {
    fontSize: "16px",
    color: "#64748b",
    margin: 0,
    maxWidth: "650px",
    marginLeft: "auto",
    marginRight: "auto",
  },
  card: {
    backgroundColor: "#ffffff",
    borderRadius: "14px",
    padding: "24px 28px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05), 0 10px 15px -3px rgba(0,0,0,0.03)",
    marginBottom: "20px",
    border: "1px solid #e2e8f0",
  },
  label: {
    display: "block",
    fontSize: "14px",
    fontWeight: "700",
    color: "#334155",
    marginBottom: "10px",
  },
  inputRow: {
    display: "flex",
    gap: "12px",
  },
  input: {
    flex: 1,
    padding: "14px 18px",
    fontSize: "15px",
    borderRadius: "8px",
    border: "1.5px solid #cbd5e1",
    outline: "none",
    transition: "border-color 0.2s",
  },
  button: {
    padding: "14px 28px",
    fontSize: "15px",
    fontWeight: "700",
    color: "#ffffff",
    backgroundColor: "#0f172a",
    border: "none",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "background-color 0.2s",
  },

  stageBox: {
    marginTop: "16px",
    padding: "12px 16px",
    backgroundColor: "#eff6ff",
    borderRadius: "8px",
    color: "#1e40af",
    fontSize: "14px",
    display: "flex",
    alignItems: "center",
    gap: "10px",
    border: "1px solid #bfdbfe",
  },
  spinner: {
    width: "16px",
    height: "16px",
    border: "2px solid #bfdbfe",
    borderTopColor: "#1d4ed8",
    borderRadius: "50%",
    animation: "spin 0.8s linear infinite",
    flexShrink: 0,
    display: "inline-block",
    boxSizing: "border-box",
  },
  errorBox: {
    marginTop: "16px",
    padding: "12px 16px",
    backgroundColor: "#fef2f2",
    borderRadius: "8px",
    color: "#991b1b",
    fontSize: "14px",
    border: "1px solid #fecaca",
  },
  scanMetaCard: {
    backgroundColor: "#f1f5f9",
    borderRadius: "10px",
    padding: "12px 20px",
    fontSize: "13px",
    color: "#475569",
    marginBottom: "20px",
    border: "1px solid #e2e8f0",
  },
  code: {
    fontFamily: "monospace",
    backgroundColor: "#e2e8f0",
    padding: "2px 6px",
    borderRadius: "4px",
    color: "#0f172a",
  },
  categoryBadge: {
    backgroundColor: "#e0f2fe",
    color: "#0369a1",
    padding: "4px 8px",
    borderRadius: "6px",
    fontWeight: "700",
    fontSize: "12px",
  },
  metricsGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "16px",
    marginBottom: "20px",
  },
  metricCard: {
    backgroundColor: "#ffffff",
    borderRadius: "14px",
    padding: "20px 24px",
    boxShadow: "0 1px 3px rgba(0,0,0,0.05)",
    border: "1px solid #e2e8f0",
  },
  metricTitle: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#64748b",
    textTransform: "uppercase",
    letterSpacing: "0.05em",
  },
  metricValue: {
    fontSize: "32px",
    fontWeight: "800",
    margin: "8px 0 4px 0",
    letterSpacing: "-0.02em",
  },
  metricSub: {
    fontSize: "13px",
    color: "#64748b",
  },
  sectionHeading: {
    fontSize: "18px",
    fontWeight: "700",
    color: "#0f172a",
    margin: 0,
  },
  breakdownGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))",
    gap: "12px",
    marginTop: "16px",
  },
  breakdownItem: {
    backgroundColor: "#f8fafc",
    padding: "12px 16px",
    borderRadius: "8px",
  },
  breakdownCount: {
    fontSize: "24px",
    fontWeight: "700",
    color: "#0f172a",
  },
  breakdownLabel: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#64748b",
    marginTop: "2px",
  },
  tabContainer: {
    display: "flex",
    gap: "6px",
    flexWrap: "wrap",
  },
  tab: {
    padding: "6px 12px",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "6px",
    border: "1px solid #e2e8f0",
    backgroundColor: "#f8fafc",
    color: "#64748b",
    cursor: "pointer",
  },
  tabActive: {
    padding: "6px 12px",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "6px",
    border: "1px solid #0f172a",
    backgroundColor: "#0f172a",
    color: "#ffffff",
    cursor: "pointer",
  },
  findingsHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "12px",
    marginBottom: "16px",
  },
  controlsRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "12px",
    paddingBottom: "16px",
    borderBottom: "1px solid #f1f5f9",
  },
  actionBtn: {
    padding: "6px 14px",
    fontSize: "12px",
    fontWeight: "600",
    borderRadius: "6px",
    border: "1px solid #cbd5e1",
    backgroundColor: "#ffffff",
    color: "#334155",
    cursor: "pointer",
    transition: "all 0.15s ease",
  },
  searchWrapper: {
    display: "flex",
    alignItems: "center",
    position: "relative",
    minWidth: "260px",
  },
  searchIcon: {
    position: "absolute",
    left: "10px",
    fontSize: "13px",
    pointerEvents: "none",
    color: "#94a3b8",
  },
  searchInput: {
    padding: "7px 28px 7px 32px",
    fontSize: "13px",
    borderRadius: "6px",
    border: "1px solid #cbd5e1",
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
    color: "#94a3b8",
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
    backgroundColor: "#f8fafc",
    borderRadius: "8px",
    border: "1px dashed #cbd5e1",
  },
  accordionContainer: {
    marginBottom: "10px",
  },
  accordionRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "12px 18px",
    backgroundColor: "#ffffff",
    border: "1px solid #e2e8f0",
    borderRadius: "8px",
    cursor: "pointer",
    transition: "background-color 0.15s ease, border-color 0.15s ease",
    userSelect: "none",
  },
  accordionRowExpanded: {
    borderBottomLeftRadius: 0,
    borderBottomRightRadius: 0,
    marginBottom: 0,
    backgroundColor: "#f8fafc",
    borderColor: "#cbd5e1",
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
    color: "#64748b",
    transition: "transform 0.15s ease",
    display: "inline-block",
    width: "12px",
    textAlign: "center",
  },
  lawBadge: {
    fontSize: "11px",
    fontWeight: "700",
    padding: "2px 8px",
    borderRadius: "4px",
    border: "1px solid",
    letterSpacing: "0.02em",
    whiteSpace: "nowrap",
  },
  refBadge: {
    fontSize: "12px",
    fontWeight: "600",
    color: "#475569",
    backgroundColor: "#f1f5f9",
    padding: "2px 8px",
    borderRadius: "4px",
    border: "1px solid #e2e8f0",
    whiteSpace: "nowrap",
  },
  actTitleText: {
    fontSize: "14px",
    fontWeight: "600",
    color: "#0f172a",
    lineHeight: "1.4",
  },
  statusBadge: {
    padding: "5px 12px",
    borderRadius: "6px",
    fontSize: "12px",
    fontWeight: "700",
    whiteSpace: "nowrap",
    letterSpacing: "0.02em",
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
  },
  accordionBody: {
    backgroundColor: "#f8fafc",
    border: "1px solid #cbd5e1",
    borderTop: "none",
    borderBottomLeftRadius: "8px",
    borderBottomRightRadius: "8px",
    padding: "16px",
    boxShadow: "inset 0 2px 4px rgba(0, 0, 0, 0.02)",
  },
  scannerGrid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    gap: "12px",
  },
  scannerCard: {
    backgroundColor: "#ffffff",
    borderRadius: "8px",
    border: "1px solid #e2e8f0",
    padding: "12px 14px",
    display: "flex",
    flexDirection: "column",
  },
  scannerCardHeader: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginBottom: "8px",
    paddingBottom: "6px",
    borderBottom: "1px solid #f1f5f9",
  },
  scannerCardIcon: {
    fontSize: "16px",
  },
  scannerCardTitle: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#1e293b",
    textTransform: "uppercase",
    letterSpacing: "0.03em",
  },
  scannerCardSub: {
    fontSize: "10px",
    color: "#94a3b8",
    fontWeight: "500",
  },
  scannerCardContent: {
    fontSize: "13px",
    color: "#334155",
    lineHeight: "1.55",
    flex: 1,
  },
  evidenceEmptyBox: {
    fontSize: "12px",
    color: "#64748b",
    fontStyle: "italic",
    padding: "4px 0",
  },
  evidenceElementRow: {
    backgroundColor: "#f8fafc",
    padding: "8px 10px",
    borderRadius: "6px",
    borderLeft: "3px solid #3b82f6",
  },
  evidenceElementName: {
    fontSize: "12px",
    fontWeight: "700",
    color: "#1e40af",
  },
  evidenceSourceTag: {
    fontSize: "10px",
    fontWeight: "600",
    backgroundColor: "#e2e8f0",
    color: "#475569",
    padding: "1px 5px",
    borderRadius: "3px",
  },
  evidenceQuoteText: {
    fontSize: "12px",
    color: "#475569",
    marginTop: "4px",
    fontStyle: "italic",
    lineHeight: "1.4",
    wordBreak: "break-word",
  },
  disclaimerCard: {
    backgroundColor: "#fefce8",
    border: "1px solid #fef08a",
    borderRadius: "12px",
    padding: "16px 20px",
    fontSize: "12px",
    color: "#713f12",
    marginBottom: "30px",
  },
};

export default App;