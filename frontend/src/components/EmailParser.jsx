import { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const SAMPLES = {
  "Loan delay": `From: david.reyes@primemortgage.com
Subject: RE: 4821 Westheimer — Loan Commitment Delay

The underwriter needs 12-month bank statements and updated pay stubs for Marcus Lin before issuing the loan commitment. Estimating 5-7 business days. Commitment deadline is April 28th — we may need an extension from the seller.`,

  "Missing inspection": `From: jennifer.walsh@houstonhomes.com
Subject: Inspection report — still waiting

We scheduled the inspection at 4821 Westheimer on April 18th with TrustCheck Inspections but have NOT received the report. Inspection contingency expires April 29th. Please follow up: 713-555-0198. Buyer Marcus Lin is anxious. Also confirm seller's response on HVAC repair.`,

  "Title issue": `From: accounts@alliedtitle.com
Subject: Title Commitment — Exception found

Title search complete. Open lien of $4,200 from Rodriguez Roofing (filed March 2, 2024). Seller must clear before closing May 3rd. Seller's attorney should address immediately or closing will be delayed.`,
};

const Tag = ({ children, type }) => {
  const colors = {
    party:  { bg: "#EEEDFE", color: "#534AB7" },
    doc:    { bg: "#E6F1FB", color: "#185FA5" },
    dl:     { bg: "#FAEEDA", color: "#854F0B" },
    action: { bg: "#FCEBEB", color: "#A32D2D" },
    ok:     { bg: "#EAF3DE", color: "#3B6D11" },
  };
  const c = colors[type] || colors.ok;
  return (
    <span style={{
      ...c, fontSize: 11, padding: "2px 8px",
      borderRadius: 99, display: "inline-block",
      margin: "2px 2px 0 0",
    }}>{children}</span>
  );
};

const Field = ({ label, children }) => (
  <div style={{ marginBottom: 10 }}>
    <div style={{ fontSize: 10, letterSpacing: 0.5, textTransform: "uppercase", color: "#999", marginBottom: 4 }}>
      {label}
    </div>
    <div>{children}</div>
  </div>
);

export default function EmailParser() {
  const [body, setBody] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const healthStyle = (h) => {
    if (!h) return {};
    if (h === "Green")  return { background: "#EAF3DE", color: "#3B6D11" };
    if (h === "Yellow") return { background: "#FAEEDA", color: "#854F0B" };
    return                     { background: "#FCEBEB", color: "#A32D2D" };
  };

  const parse = async () => {
    if (!body.trim()) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await fetch(`${API}/parse-email`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ body }),
      });
      if (!res.ok) throw new Error(await res.text());
      setResult(await res.json());
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontFamily: "Fraunces, serif", fontWeight: 300, fontSize: 26, marginBottom: 4 }}>
        Email → Deal Room
      </h1>
      <p style={{ fontSize: 12, color: "#888", marginBottom: 24 }}>
        Paste any real estate email. Claude extracts parties, docs, deadlines, and deal health.
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
        {/* Input */}
        <div>
          <div style={{ fontSize: 10, letterSpacing: 0.8, textTransform: "uppercase", color: "#999", marginBottom: 6 }}>
            Raw email
          </div>
          <textarea
            value={body}
            onChange={e => setBody(e.target.value)}
            placeholder="Paste email body here…"
            style={{
              width: "100%", height: 200, resize: "none",
              background: "#fff", border: "0.5px solid #ddd",
              borderRadius: 8, padding: "10px 12px",
              fontFamily: "DM Mono, monospace", fontSize: 12,
              lineHeight: 1.6, outline: "none",
            }}
          />

          {/* Sample buttons */}
          <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
            {Object.entries(SAMPLES).map(([label, text]) => (
              <button key={label} onClick={() => setBody(text)} style={{
                fontSize: 10, padding: "4px 10px", borderRadius: 6,
                border: "0.5px solid #ccc", background: "none",
                color: "#666", cursor: "pointer",
                fontFamily: "DM Mono, monospace",
              }}>
                sample: {label}
              </button>
            ))}
          </div>

          <button
            onClick={parse}
            disabled={loading || !body.trim()}
            style={{
              width: "100%", marginTop: 10, padding: 10,
              background: loading ? "#ccc" : "#1D9E75",
              color: "#fff", border: "none", borderRadius: 8,
              fontFamily: "DM Mono, monospace", fontSize: 12,
              fontWeight: 500, cursor: loading ? "not-allowed" : "pointer",
            }}
          >
            {loading ? "parsing with claude…" : "→ parse with claude"}
          </button>
          {error && (
            <div style={{ marginTop: 8, fontSize: 11, color: "#A32D2D", background: "#FCEBEB", padding: 8, borderRadius: 6 }}>
              {error}
            </div>
          )}
        </div>

        {/* Result */}
        <div style={{
          background: "#fff", border: "0.5px solid #e5e5e5",
          borderRadius: 12, padding: 16, minHeight: 200,
        }}>
          {!result && !loading && (
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 200, color: "#bbb", fontSize: 12 }}>
              results appear here
            </div>
          )}
          {loading && (
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#888" }}>
              <span>claude is reading the email</span>
              <span style={{ letterSpacing: 2 }}>...</span>
            </div>
          )}
          {result && (
            <>
              <div style={{
                ...healthStyle(result.deal_health),
                padding: "6px 12px", borderRadius: 8,
                fontSize: 12, fontWeight: 500, marginBottom: 12,
                display: "flex", alignItems: "center", gap: 6,
              }}>
                ● {result.deal_health} — {result.health_reason}
              </div>
              <Field label="Summary">
                <span style={{ fontSize: 12, lineHeight: 1.5 }}>{result.subject_summary}</span>
              </Field>
              <Field label="Parties">
                {result.parties?.map((p, i) => <Tag key={i} type="party">{p}</Tag>)}
              </Field>
              <Field label="Documents">
                {result.documents?.map((d, i) => <Tag key={i} type="doc">{d}</Tag>)}
              </Field>
              <Field label="Deadlines">
                {result.deadlines?.map((d, i) => <Tag key={i} type="dl">{d}</Tag>)}
              </Field>
              <Field label="Action items">
                {result.action_items?.map((a, i) => <Tag key={i} type="action">{a}</Tag>)}
              </Field>
              {result.missing_docs?.length > 0 && (
                <Field label="⚠ Missing docs">
                  {result.missing_docs.map((d, i) => <Tag key={i} type="action">{d}</Tag>)}
                </Field>
              )}
              {result.follow_up_draft && (
                <Field label="AI follow-up draft">
                  <div style={{
                    fontSize: 11, background: "#f5f5f0",
                    padding: "8px 10px", borderRadius: 6,
                    lineHeight: 1.7, color: "#444",
                  }}>
                    {result.follow_up_draft}
                  </div>
                </Field>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
