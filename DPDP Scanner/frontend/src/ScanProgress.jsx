import React, { useEffect, useState, useRef } from "react";

export const PIPELINE_STEPS = [
  {
    id: 1,
    phase: 1,
    phaseTitle: "Web Crawling & Evidence Gathering",
    title: "Target Handshake & SSL / Security Verification",
    desc: "Validating domain DNS, TLS certificate, and HTTP transport security",
    tag: "Sec 8(5) Safeguards",
    detail: "Establishing TLS 1.3 tunnel and verifying server security headers...",
  },
  {
    id: 2,
    phase: 1,
    phaseTitle: "Web Crawling & Evidence Gathering",
    title: "Headless Browser Engine & DOM Tree Capture",
    desc: "Launching sandboxed Playwright engine to inspect dynamic client-side DOM",
    tag: "Evidence Snapshot",
    detail: "Rendering interactive DOM tree, dynamic scripts, and visual components...",
  },
  {
    id: 3,
    phase: 1,
    phaseTitle: "Web Crawling & Evidence Gathering",
    title: "Tracking Cookies & Third-Party Tags Audit",
    desc: "Auditing browser cookies, tracker patterns (_ga, _fbp), and marketing beacons",
    tag: "Sec 6(1) Notice",
    detail: "Screening storage for analytics beacons, session cookies, and third-party trackers...",
  },
  {
    id: 4,
    phase: 1,
    phaseTitle: "Web Crawling & Evidence Gathering",
    title: "Personal Data Intake & Web Form Discovery",
    desc: "Detecting input forms collecting personal data (Name, Phone, Email, DOB, ID)",
    tag: "Sec 6 Consent",
    detail: "Parsing input fields, consent checkboxes, and voluntary data intake points...",
  },
  {
    id: 5,
    phase: 1,
    phaseTitle: "Web Crawling & Evidence Gathering",
    title: "Statutory Disclosures & Grievance Officer Scan",
    desc: "Locating Privacy Policy, Terms of Service, DPO / Grievance Officer contacts & notices",
    tag: "Sec 8 & Rules 2025",
    detail: "Extracting Privacy Notice clauses, Grievance Officer contact details, and PDF documents...",
  },
  {
    id: 6,
    phase: 1,
    phaseTitle: "Web Crawling & Evidence Gathering",
    title: "MongoDB Atlas Evidence Ingestion",
    desc: "Packaging evidentiary snapshot into persistent database repository",
    tag: "Persistence Layer",
    detail: "Serializing DOM evidence, extracted fields, and cookies to MongoDB Atlas cluster...",
  },
  {
    id: 7,
    phase: 2,
    phaseTitle: "DPDP AI & Legal Compliance Evaluation",
    title: "Entity Domain & Fiduciary Classification",
    desc: "Classifying business domain & significant data fiduciary criteria (Sec 2(i) / 2(z))",
    tag: "Sec 10 SDF Check",
    detail: "Determining data fiduciary archetype, sector classifications, and statutory exemptions...",
  },
  {
    id: 8,
    phase: 2,
    phaseTitle: "DPDP AI & Legal Compliance Evaluation",
    title: "DPDP Act 2023 & Rules 2025 Legal RAG Retrieval",
    desc: "Vector search across statutory rules, exemptions, and statutory mandates",
    tag: "Vectorstore RAG",
    detail: "Aligning extracted website evidence with 47 statutory requirements and phased timelines...",
  },
  {
    id: 9,
    phase: 2,
    phaseTitle: "DPDP AI & Legal Compliance Evaluation",
    title: "Gemini 3.1 Semantic Evidence Reasoning",
    desc: "Running AI compliance evaluation across all statutory provisions",
    tag: "Gemini 3.1 Flash",
    detail: "Evaluating statutory notice clarity, consent validity, and data retention disclosures...",
  },
  {
    id: 10,
    phase: 2,
    phaseTitle: "DPDP AI & Legal Compliance Evaluation",
    title: "Compliance Scorecard & Findings Synthesis",
    desc: "Synthesizing penalty risk matrix, evidence coverage metrics, and actionable report",
    tag: "Audit Synthesis",
    detail: "Computing deterministic compliance score and generating section-by-section audit report...",
  },
];

export default function ModernScanProgress({
  websiteUrl,
  currentStepIndex,
  isPhaseTwo,
  hasError,
  errorMessage,
}) {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [showTelemetry, setShowTelemetry] = useState(false);
  const telemetryEndRef = useRef(null);

  // Live timer
  useEffect(() => {
    const startTime = Date.now();
    const interval = setInterval(() => {
      setElapsedSeconds(Math.floor((Date.now() - startTime) / 1000));
    }, 200);
    return () => clearInterval(interval);
  }, []);

  // Telemetry auto-scroll
  useEffect(() => {
    if (showTelemetry && telemetryEndRef.current) {
      telemetryEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [currentStepIndex, elapsedSeconds, showTelemetry]);

  // Compute progress percentage smoothly
  const progressPercent = Math.min(
    98,
    Math.max(
      8,
      Math.round(
        ((currentStepIndex + 0.6) / PIPELINE_STEPS.length) * 100
      )
    )
  );

  const formatTime = (secs) => {
    const m = Math.floor(secs / 60);
    const s = secs % 60;
    return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
  };

  const currentStep = PIPELINE_STEPS[currentStepIndex] || PIPELINE_STEPS[0];

  return (
    <div style={styles.container}>
      {/* TOP STATUS BAR */}
      <div style={styles.statusBar}>
        <div style={styles.targetInfo}>
          <div style={styles.livePulseDot} />
          <span style={styles.liveAuditText}>LIVE COMPLIANCE AUDIT</span>
          <span style={styles.targetDivider}>•</span>
          <span style={styles.targetUrlText}>
            {websiteUrl || "Target Website"}
          </span>
        </div>

        <div style={styles.timeAndProgressStats}>
          {/* JUST TIMER RUNNING */}
          <div style={styles.timerRunningPill} title="Live scan timer running">
            <span style={styles.timerPulseDot} />
            <span style={styles.timerRunningText}>Timer running:</span>
            <span style={styles.timerRunningValue}>{formatTime(elapsedSeconds)}s</span>
          </div>

          <div style={styles.progressPill}>
            <span style={styles.progressLabel}>PROGRESS</span>
            <span style={styles.progressValue}>{progressPercent}%</span>
          </div>
        </div>
      </div>

      {/* CLEAN EXECUTIVE PROGRESS HERO SECTION (WITHOUT RADAR ANIMATION) */}
      <div style={styles.scannerHeroSection}>
        <div style={styles.activeHeadlineBlock}>
          <div style={styles.phaseBadgeRow}>
            <span style={styles.phaseBadge}>
              <span style={styles.pulseDotCyan} />
              {currentStep.phase === 1
                ? "PHASE 1: FORENSIC WEB CRAWLER & EVIDENCE DISCOVERY"
                : "PHASE 2: GEMINI 3.1 AI & LEGAL RAG EVALUATION"}
            </span>
            <span style={styles.stepCounterBadge}>
              Step {currentStepIndex + 1} of {PIPELINE_STEPS.length}
            </span>
          </div>

          <div style={styles.stepHeaderLine}>
            <h3 style={styles.currentStepTitle}>{currentStep.title}</h3>
            <span style={styles.currentStepTag}>{currentStep.tag}</span>
          </div>

          <p style={styles.currentStepDetail}>{currentStep.detail}</p>

          {/* Precision Progress Bar */}
          <div style={styles.progressBarWrapper}>
            <div style={styles.progressBarTrack}>
              <div
                style={{
                  ...styles.progressBarFill,
                  width: `${progressPercent}%`,
                }}
              />
            </div>
            <div style={styles.progressPercentText}>{progressPercent}%</div>
          </div>
        </div>
      </div>

      {/* CONTINUOUS STEPS PIPELINE (LIST OF ALL 10 STEPS - DARK THEME) */}
      <div style={styles.stepsSection}>
        <div style={styles.stepsHeader}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <span style={styles.sectionIcon}>⚡</span>
            <span style={styles.stepsHeadingText}>
              Statutory Verification Pipeline
            </span>
          </div>
          <span style={styles.pipelineSub}>
            Automated screening against DPDP Act 2023 & DPDP Rules 2025
          </span>
        </div>

        <div style={styles.stepsList}>
          {PIPELINE_STEPS.map((step, idx) => {
            const isCompleted = idx < currentStepIndex;
            const isCurrent = idx === currentStepIndex && !hasError;
            const isPending = idx > currentStepIndex;
            const isFailed = idx === currentStepIndex && hasError;

            return (
              <div
                key={step.id}
                style={{
                  ...styles.stepRow,
                  ...(isCurrent ? styles.stepRowCurrent : {}),
                  ...(isCompleted ? styles.stepRowCompleted : {}),
                }}
              >
                {/* Step Connector Line */}
                {idx < PIPELINE_STEPS.length - 1 && (
                  <div
                    style={{
                      ...styles.connectorLine,
                      backgroundColor: isCompleted
                        ? "#0f766e"
                        : "#e2e8f0",
                    }}
                  />
                )}

                {/* Left Step Status Icon */}
                <div style={styles.iconContainer}>
                  {isCompleted && (
                    <div style={styles.completedBadge} title="Completed">
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#ffffff"
                        strokeWidth="3"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    </div>
                  )}

                  {isCurrent && (
                    <div style={styles.activeOrbitalBadge}>
                      <div style={styles.activeCoreDot} />
                    </div>
                  )}

                  {isPending && (
                    <div style={styles.pendingBadge}>
                      <span>{step.id}</span>
                    </div>
                  )}

                  {isFailed && (
                    <div style={styles.failedBadge}>
                      <span>✕</span>
                    </div>
                  )}
                </div>

                {/* Step Text Info */}
                <div style={styles.stepContent}>
                  <div style={styles.stepTitleRow}>
                    <span
                      style={{
                        ...styles.stepTitle,
                        color: isCurrent
                          ? "#0f766e"
                          : isCompleted
                          ? "#0f172a"
                          : "#64748b",
                        fontWeight: isCurrent ? "700" : isCompleted ? "600" : "500",
                      }}
                    >
                      {step.title}
                    </span>

                    <span
                      style={{
                        ...styles.stepTag,
                        backgroundColor: isCurrent
                          ? "rgba(212, 175, 55, 0.15)"
                          : isCompleted
                          ? "rgba(15, 118, 110, 0.1)"
                          : "#f1f5f9",
                        color: isCurrent
                          ? "#854d0e"
                          : isCompleted
                          ? "#0f766e"
                          : "#64748b",
                        borderColor: isCurrent
                          ? "rgba(212, 175, 55, 0.4)"
                          : isCompleted
                          ? "rgba(15, 118, 110, 0.3)"
                          : "#e2e8f0",
                      }}
                    >
                      {step.tag}
                    </span>

                    {isCurrent && (
                      <span style={styles.inProgressPill}>
                        <span style={styles.inProgressDot} />
                        Active
                      </span>
                    )}

                    {isCompleted && (
                      <span style={styles.donePill}>Verified ✓</span>
                    )}
                  </div>

                  <p
                    style={{
                      ...styles.stepDesc,
                      color: isCurrent ? "#334155" : isCompleted ? "#475569" : "#94a3b8",
                    }}
                  >
                    {isCurrent ? step.detail : step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* LIVE AUDIT TELEMETRY TERMINAL (COLLAPSIBLE / HIDDEN BY DEFAULT) */}
      <div style={styles.terminalContainer}>
        <div
          onClick={() => setShowTelemetry((prev) => !prev)}
          style={{
            ...styles.terminalHeader,
            cursor: "pointer",
            userSelect: "none",
          }}
          title={showTelemetry ? "Click to hide console logs" : "Click to view real-time audit logs"}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={styles.terminalDots}>
              <span style={{ ...styles.terminalDot, backgroundColor: "#ef4444" }} />
              <span style={{ ...styles.terminalDot, backgroundColor: "#f59e0b" }} />
              <span style={{ ...styles.terminalDot, backgroundColor: "#10b981" }} />
            </div>
            <span style={styles.terminalTitle}>
              AUDIT TELEMETRY STREAM & FORENSIC EVENT LOG
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <span style={styles.terminalLiveBadge}>
              {currentStepIndex + 1} EVENTS
            </span>
            <span style={styles.terminalToggleBtn}>
              {showTelemetry ? "Hide Console ▲" : "Show Console ▼"}
            </span>
          </div>
        </div>

        {showTelemetry && (
          <div className="telemetry-scroll" style={styles.terminalBody}>
            <div style={styles.terminalLine}>
              <span style={styles.termTimestamp}>[00:00.0]</span>
              <span style={styles.termTagInit}>[ENGINE_INIT]</span>
              <span style={styles.termText}>
                Compliance scanner initialized. Connecting to {websiteUrl}...
              </span>
            </div>

            {PIPELINE_STEPS.slice(0, currentStepIndex + 1).map((s, i) => (
              <div key={i} style={styles.terminalLine}>
                <span style={styles.termTimestamp}>
                  [{formatTime(Math.min(elapsedSeconds, (i + 1) * 2))}.
                  {((i * 3 + 2) % 9) + 1}]
                </span>
                <span
                  style={
                    i < currentStepIndex
                      ? styles.termTagComplete
                      : styles.termTagActive
                  }
                >
                  {i < currentStepIndex ? "[AUDITED]" : "[RUNNING]"}
                </span>
                <span
                  style={{
                    ...styles.termText,
                    color: i === currentStepIndex ? "#38bdf8" : "#94a3b8",
                  }}
                >
                  {s.detail}
                </span>
              </div>
            ))}

            {hasError && (
              <div style={styles.terminalLine}>
                <span style={styles.termTimestamp}>[{formatTime(elapsedSeconds)}]</span>
                <span style={styles.termTagError}>[ERROR]</span>
                <span style={{ ...styles.termText, color: "#f87171" }}>
                  {errorMessage || "Inspection encountered a communication exception."}
                </span>
              </div>
            )}

            <div style={styles.terminalActiveLine}>
              <span style={styles.termPrompt}>&gt;</span>
              <span style={styles.termTextActive}>
                {hasError
                  ? "Scan aborted. Please review connection or domain address."
                  : currentStep.detail}
              </span>
              <span style={styles.cursorBlink}>_</span>
            </div>
            <div ref={telemetryEndRef} />
          </div>
        )}
      </div>
    </div>
  );
}

const styles = {
  container: {
    backgroundColor: "rgba(255, 255, 255, 0.96)",
    backdropFilter: "blur(20px)",
    borderRadius: "18px",
    border: "1px solid rgba(212, 175, 55, 0.35)",
    boxShadow: "0 20px 45px -10px rgba(15, 23, 42, 0.08), 0 0 0 1px rgba(212, 175, 55, 0.15)",
    marginTop: "20px",
    overflow: "hidden",
    animation: "fadeInSlide 0.3s ease-out",
  },
  statusBar: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    padding: "14px 22px",
    backgroundColor: "#ffffff",
    color: "#0f172a",
    flexWrap: "wrap",
    gap: "12px",
    borderBottom: "1px solid rgba(212, 175, 55, 0.22)",
  },
  targetInfo: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    flexWrap: "wrap",
  },
  livePulseDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: "#0d9488",
    boxShadow: "0 0 10px #0d9488",
    animation: "stepGlow 1.8s infinite",
  },
  liveAuditText: {
    fontSize: "11px",
    fontWeight: "800",
    letterSpacing: "0.08em",
    color: "#0f766e",
  },
  targetDivider: {
    color: "#cbd5e1",
    fontSize: "12px",
  },
  targetUrlText: {
    fontSize: "13px",
    fontWeight: "600",
    color: "#0f172a",
    fontFamily: "'JetBrains Mono', monospace",
    backgroundColor: "rgba(15, 118, 110, 0.06)",
    padding: "3px 10px",
    borderRadius: "6px",
    border: "1px solid rgba(212, 175, 55, 0.35)",
  },
  timeAndProgressStats: {
    display: "flex",
    gap: "12px",
    alignItems: "center",
  },
  timerRunningPill: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    backgroundColor: "rgba(254, 243, 199, 0.75)",
    padding: "5px 13px",
    borderRadius: "20px",
    border: "1px solid rgba(217, 119, 6, 0.4)",
    boxShadow: "0 2px 8px rgba(217, 119, 6, 0.12)",
  },
  timerPulseDot: {
    width: "7px",
    height: "7px",
    borderRadius: "50%",
    backgroundColor: "#d97706",
    boxShadow: "0 0 8px #d97706",
    animation: "liveTimerPulse 1.6s infinite ease-in-out",
  },
  timerRunningText: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#92400e",
    letterSpacing: "0.04em",
    textTransform: "uppercase",
  },
  timerRunningValue: {
    fontSize: "13px",
    fontWeight: "800",
    color: "#78350f",
    fontFamily: "'JetBrains Mono', monospace",
    letterSpacing: "0.05em",
  },
  progressPill: {
    display: "flex",
    alignItems: "center",
    gap: "7px",
    backgroundColor: "rgba(15, 118, 110, 0.09)",
    padding: "5px 13px",
    borderRadius: "20px",
    border: "1px solid rgba(15, 118, 110, 0.3)",
    boxShadow: "0 2px 8px rgba(15, 118, 110, 0.08)",
  },
  progressLabel: {
    fontSize: "10px",
    fontWeight: "700",
    color: "#0f766e",
    letterSpacing: "0.06em",
  },
  progressValue: {
    fontSize: "13px",
    fontWeight: "800",
    color: "#0f766e",
    fontFamily: "'JetBrains Mono', monospace",
  },

  /* CLEAN PROGRESS HERO SECTION */
  scannerHeroSection: {
    padding: "24px 28px",
    background: "linear-gradient(135deg, rgba(240, 253, 250, 0.85) 0%, rgba(254, 252, 232, 0.7) 100%)",
    borderBottom: "1px solid rgba(212, 175, 55, 0.22)",
  },
  activeHeadlineBlock: {
    width: "100%",
  },
  phaseBadgeRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "8px",
    marginBottom: "10px",
    flexWrap: "wrap",
  },
  phaseBadge: {
    display: "inline-flex",
    alignItems: "center",
    gap: "6px",
    fontSize: "11px",
    fontWeight: "700",
    color: "#0f766e",
    backgroundColor: "rgba(15, 118, 110, 0.1)",
    padding: "4px 12px",
    borderRadius: "6px",
    letterSpacing: "0.05em",
    border: "1px solid rgba(15, 118, 110, 0.3)",
  },
  pulseDotCyan: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    backgroundColor: "#0d9488",
    boxShadow: "0 0 6px #0d9488",
    animation: "stepGlow 1.5s infinite",
  },
  stepCounterBadge: {
    fontSize: "11px",
    fontWeight: "600",
    color: "#334155",
    backgroundColor: "#ffffff",
    padding: "3px 10px",
    borderRadius: "6px",
    border: "1px solid rgba(212, 175, 55, 0.3)",
  },
  stepHeaderLine: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    gap: "12px",
    flexWrap: "wrap",
    marginBottom: "6px",
  },
  currentStepTitle: {
    fontSize: "20px",
    fontWeight: "800",
    color: "#0f172a",
    margin: 0,
    letterSpacing: "-0.01em",
  },
  currentStepTag: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#854d0e",
    backgroundColor: "rgba(212, 175, 55, 0.15)",
    padding: "3px 9px",
    borderRadius: "4px",
    border: "1px solid rgba(212, 175, 55, 0.4)",
    letterSpacing: "0.03em",
  },
  currentStepDetail: {
    fontSize: "14px",
    color: "#475569",
    margin: "0 0 16px 0",
    lineHeight: "1.5",
  },
  progressBarWrapper: {
    display: "flex",
    alignItems: "center",
    gap: "14px",
  },
  progressBarTrack: {
    flex: 1,
    height: "8px",
    backgroundColor: "#e2e8f0",
    borderRadius: "4px",
    overflow: "hidden",
    position: "relative",
    border: "1px solid rgba(212, 175, 55, 0.25)",
  },
  progressBarFill: {
    height: "100%",
    background: "linear-gradient(90deg, #0d9488 0%, #0f766e 60%, #d4af37 100%)",
    borderRadius: "4px",
    transition: "width 0.4s ease-out",
    backgroundSize: "200% 100%",
    animation: "shimmerWave 2s linear infinite",
  },
  progressPercentText: {
    fontSize: "13px",
    fontWeight: "700",
    color: "#0f766e",
    fontFamily: "'JetBrains Mono', monospace",
    minWidth: "36px",
    textAlign: "right",
  },

  /* STEPS LIST */
  stepsSection: {
    padding: "24px 28px",
    backgroundColor: "#ffffff",
  },
  stepsHeader: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: "16px",
    flexWrap: "wrap",
    gap: "8px",
  },
  sectionIcon: {
    fontSize: "16px",
  },
  stepsHeadingText: {
    fontSize: "15px",
    fontWeight: "700",
    color: "#0f172a",
  },
  pipelineSub: {
    fontSize: "12px",
    color: "#64748b",
  },
  stepsList: {
    display: "flex",
    flexDirection: "column",
    gap: "3px",
    position: "relative",
  },
  stepRow: {
    display: "flex",
    alignItems: "flex-start",
    gap: "16px",
    padding: "12px 14px",
    borderRadius: "10px",
    position: "relative",
    transition: "all 0.2s ease",
  },
  stepRowCurrent: {
    backgroundColor: "rgba(240, 253, 250, 0.85)",
    border: "1px solid rgba(212, 175, 55, 0.45)",
    boxShadow: "0 2px 10px rgba(212, 175, 55, 0.12)",
  },
  stepRowCompleted: {
    backgroundColor: "transparent",
  },
  connectorLine: {
    position: "absolute",
    left: "27px",
    top: "36px",
    width: "2px",
    height: "calc(100% - 14px)",
    zIndex: 1,
    transition: "background-color 0.3s ease",
  },
  iconContainer: {
    position: "relative",
    zIndex: 2,
    flexShrink: 0,
    marginTop: "2px",
  },
  completedBadge: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    backgroundColor: "#0f766e",
    border: "1.5px solid #0d9488",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 2px 8px rgba(15, 118, 110, 0.2)",
  },
  activeOrbitalBadge: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    backgroundColor: "#ffffff",
    border: "2px solid #d4af37",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    boxShadow: "0 0 12px rgba(212, 175, 55, 0.4)",
    animation: "stepGlow 1.8s infinite",
  },
  activeCoreDot: {
    width: "8px",
    height: "8px",
    borderRadius: "50%",
    backgroundColor: "#b45309",
  },
  pendingBadge: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    backgroundColor: "#f1f5f9",
    border: "1px solid #cbd5e1",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontSize: "12px",
    fontWeight: "700",
    color: "#64748b",
  },
  failedBadge: {
    width: "28px",
    height: "28px",
    borderRadius: "50%",
    backgroundColor: "#ef4444",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "#ffffff",
    fontSize: "13px",
    fontWeight: "700",
  },

  stepContent: {
    flex: 1,
  },
  stepTitleRow: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    flexWrap: "wrap",
    marginBottom: "3px",
  },
  stepTitle: {
    fontSize: "14px",
    lineHeight: "1.3",
  },
  stepTag: {
    fontSize: "10px",
    fontWeight: "700",
    padding: "1px 6px",
    borderRadius: "4px",
    border: "1px solid",
    letterSpacing: "0.02em",
  },
  inProgressPill: {
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    fontSize: "10px",
    fontWeight: "700",
    color: "#0f766e",
    backgroundColor: "rgba(15, 118, 110, 0.1)",
    padding: "2px 8px",
    borderRadius: "12px",
    marginLeft: "auto",
    border: "1px solid rgba(15, 118, 110, 0.3)",
  },
  inProgressDot: {
    width: "6px",
    height: "6px",
    borderRadius: "50%",
    backgroundColor: "#0d9488",
    animation: "stepGlow 1.4s infinite",
  },
  donePill: {
    fontSize: "11px",
    fontWeight: "600",
    color: "#0f766e",
    marginLeft: "auto",
  },
  stepDesc: {
    fontSize: "12px",
    margin: 0,
    lineHeight: "1.45",
  },

  /* TERMINAL LOGS */
  terminalContainer: {
    backgroundColor: "#0b1319",
    borderTop: "1px solid rgba(212, 175, 55, 0.28)",
  },
  terminalHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "10px 20px",
    backgroundColor: "#080e13",
    borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
  },
  terminalDots: {
    display: "flex",
    gap: "6px",
  },
  terminalDot: {
    width: "9px",
    height: "9px",
    borderRadius: "50%",
  },
  terminalTitle: {
    fontSize: "11px",
    fontWeight: "700",
    color: "#cbd5e1",
    letterSpacing: "0.06em",
    fontFamily: "'JetBrains Mono', monospace",
  },
  terminalLiveBadge: {
    fontSize: "9px",
    fontWeight: "800",
    color: "#2dd4bf",
    backgroundColor: "rgba(45, 212, 191, 0.15)",
    padding: "2px 6px",
    borderRadius: "4px",
    letterSpacing: "0.06em",
    border: "1px solid rgba(45, 212, 191, 0.35)",
  },
  terminalToggleBtn: {
    fontSize: "10px",
    fontWeight: "700",
    color: "#fef08a",
    backgroundColor: "rgba(255, 255, 255, 0.08)",
    padding: "3px 8px",
    borderRadius: "4px",
    border: "1px solid rgba(212, 175, 55, 0.35)",
    cursor: "pointer",
    display: "inline-flex",
    alignItems: "center",
    gap: "4px",
    letterSpacing: "0.03em",
    transition: "background-color 0.15s ease",
  },
  terminalBody: {
    padding: "14px 20px",
    fontFamily: "'JetBrains Mono', monospace",
    fontSize: "12px",
    lineHeight: "1.6",
    maxHeight: "160px",
    overflowY: "auto",
    color: "#cbd5e1",
    backgroundColor: "#05090c",
  },
  terminalLine: {
    display: "flex",
    gap: "8px",
    marginBottom: "4px",
    flexWrap: "wrap",
  },
  termTimestamp: {
    color: "#64748b",
  },
  termTagInit: {
    color: "#2dd4bf",
    fontWeight: "700",
  },
  termTagActive: {
    color: "#fef08a",
    fontWeight: "700",
  },
  termTagComplete: {
    color: "#34d399",
    fontWeight: "700",
  },
  termTagError: {
    color: "#f87171",
    fontWeight: "700",
  },
  termText: {
    color: "#cbd5e1",
  },
  terminalActiveLine: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    marginTop: "6px",
    color: "#2dd4bf",
  },
  termPrompt: {
    color: "#d4af37",
    fontWeight: "800",
  },
  termTextActive: {
    color: "#2dd4bf",
    fontWeight: "600",
  },
  cursorBlink: {
    color: "#d4af37",
    fontWeight: "800",
    animation: "terminalBlink 1s infinite",
  },
};
