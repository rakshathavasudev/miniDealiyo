import { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const ALL_DOCS = [
  "Purchase Agreement",
  "Inspection Report",
  "Loan Commitment Letter",
  "Title Commitment",
  "HOA Disclosure",
  "Seller Disclosure",
  "Appraisal Report",
];

export default function DealHealthCard() {
  const [address, setAddress] = useState("4821 Westheimer Rd, Houston TX");
  const [closingDate, setClosingDate] = useState("2025-05-03");
  const [receivedDocs, setReceivedDocs] = useState(["Purchase Agreement", "HOA Disclosure"]);
  const [lenderFlag, setLenderFlag] = useState(true);
  const [titleFlag, setTitleFlag] = useState(false);
  const [overdue, setOverdue] = useState("Loan commitment (Apr 25)");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggleDoc = (doc) => {
    setReceivedDocs(prev =>
      prev.includes(doc) ? prev.filter(d => d !== doc) : [...prev, doc]
    );
  };

  // Compute health locally (mirrors backend logic) for instant preview
  const computeLocal = () => {
    let score = 100;
    const reasons = [];
    const missing = ALL_DOCS.filter(d => !receivedDocs.includes(d));

    if (missing.length) {
      score -= Math.min(missing.length * 15, 40);
      reasons.push(`${missing.length} doc(s) missing`);
    }
    if (overdue.trim()) { score -= 20; reasons.push("Overdue deadline"); }
    if (lenderFlag)     { score -= 15; reasons.push("Lender flagged issue"); }
    if (titleFlag)      { score -= 20; reasons.push("Title issue"); }

    const days = Math.floor((new Date(closingDate) - new Date()) / 86400000);
    if (days < 3 && score < 90) { score -= 10; reasons.push(`${days}d to close`); }

    score = Math.max(0, score);
    const status = score >= 80 ? "Green" : score >= 50 ? "Yellow" : "Red";
    return { score, status, reasons, missing };
  };

  const local = computeLocal();

  const healthColor = (s) => {
    if (s === "Green")  return { bg: "#EAF3DE", text: "#3B6D11", dot: "#639922" };
    if (s === "Yellow") return { bg: "#FAEEDA", text: "#854F0B", dot: "#BA7517" };
    return                     { bg: "#FCEBEB", text: "#A32D2D", dot: "#E24B4A" };
  };

  const c = healthColor(local.status);

  return (
    <div>
      <h1 style={{ fontFamily: "Fraunces, serif", fontWeight: 300, fontSize: 26, marginBottom: 4 }}>
        Deal Health Engine
      </h1>
      <p style={{ fontSize: 12, color: "#888", marginBottom: 24 }}>
        Rule-based scoring + Claude recommendations. Updates live.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Controls */}
        <div style={{ background: "#fff", border: "0.5px solid #e5e5e5", borderRadius: 12, padding: 16 }}>
          <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", letterSpacing: 0.8, marginBottom: 12 }}>
            Deal signals
          </div>

          <label style={{ fontSize: 11, color: "#666", display: "block", marginBottom: 4 }}>Property address</label>
          <input value={address} onChange={e => setAddress(e.target.value)} style={{
            width: "100%", fontSize: 12, padding: "6px 10px",
            border: "0.5px solid #ddd", borderRadius: 6,
            fontFamily: "DM Mono, monospace", marginBottom: 12, outline: "none",
          }} />

          <label style={{ fontSize: 11, color: "#666", display: "block", marginBottom: 4 }}>Closing date</label>
          <input type="date" value={closingDate} onChange={e => setClosingDate(e.target.value)} style={{
            width: "100%", fontSize: 12, padding: "6px 10px",
            border: "0.5px solid #ddd", borderRadius: 6,
            fontFamily: "DM Mono, monospace", marginBottom: 12, outline: "none",
          }} />

          <label style={{ fontSize: 11, color: "#666", display: "block", marginBottom: 6 }}>Documents received</label>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 12 }}>
            {ALL_DOCS.map(doc => (
              <label key={doc} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, cursor: "pointer" }}>
                <input type="checkbox" checked={receivedDocs.includes(doc)} onChange={() => toggleDoc(doc)} />
                {doc}
              </label>
            ))}
          </div>

          <label style={{ fontSize: 11, color: "#666", display: "block", marginBottom: 4 }}>Overdue deadline (if any)</label>
          <input value={overdue} onChange={e => setOverdue(e.target.value)} style={{
            width: "100%", fontSize: 12, padding: "6px 10px",
            border: "0.5px solid #ddd", borderRadius: 6,
            fontFamily: "DM Mono, monospace", marginBottom: 12, outline: "none",
          }} />

          <div style={{ display: "flex", gap: 16 }}>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer" }}>
              <input type="checkbox" checked={lenderFlag} onChange={e => setLenderFlag(e.target.checked)} />
              Lender flag
            </label>
            <label style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, cursor: "pointer" }}>
              <input type="checkbox" checked={titleFlag} onChange={e => setTitleFlag(e.target.checked)} />
              Title flag
            </label>
          </div>
        </div>

        {/* Live score */}
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {/* Score card */}
          <div style={{
            background: c.bg, borderRadius: 12, padding: 20,
            display: "flex", alignItems: "center", gap: 16,
          }}>
            <div style={{
              width: 64, height: 64, borderRadius: "50%",
              background: "#fff", display: "flex", alignItems: "center",
              justifyContent: "center", flexShrink: 0,
            }}>
              <span style={{ fontSize: 22, fontWeight: 500, color: c.text }}>{local.score}</span>
            </div>
            <div>
              <div style={{ fontSize: 18, fontWeight: 500, color: c.text }}>{local.status}</div>
              <div style={{ fontSize: 11, color: c.text, opacity: 0.8, marginTop: 2 }}>
                {local.reasons.join(" · ") || "No issues detected"}
              </div>
            </div>
          </div>

          {/* Missing docs */}
          {local.missing.length > 0 && (
            <div style={{ background: "#fff", border: "0.5px solid #e5e5e5", borderRadius: 12, padding: 14 }}>
              <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", letterSpacing: 0.8, marginBottom: 8 }}>
                Missing documents
              </div>
              {local.missing.map(d => (
                <div key={d} style={{
                  fontSize: 12, padding: "5px 10px", marginBottom: 4,
                  background: "#FCEBEB", color: "#A32D2D", borderRadius: 6,
                  display: "flex", justifyContent: "space-between",
                }}>
                  {d}
                  <span style={{ fontSize: 10, opacity: 0.7 }}>AI follow-up queued</span>
                </div>
              ))}
            </div>
          )}

          {/* Progress bar */}
          <div style={{ background: "#fff", border: "0.5px solid #e5e5e5", borderRadius: 12, padding: 14 }}>
            <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", letterSpacing: 0.8, marginBottom: 8 }}>
              Deal completion
            </div>
            <div style={{ background: "#f0f0f0", borderRadius: 4, height: 6, overflow: "hidden" }}>
              <div style={{
                width: `${local.score}%`, height: "100%",
                background: c.dot, borderRadius: 4,
                transition: "width 0.4s ease",
              }} />
            </div>
            <div style={{ fontSize: 11, color: "#999", marginTop: 6 }}>
              {receivedDocs.length} / {ALL_DOCS.length} documents received
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
