import { useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const Field = ({ label, value }) => {
  if (!value || value === "null") return null;
  return (
    <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: "0.5px solid #f0f0f0", fontSize: 12 }}>
      <span style={{ color: "#888", minWidth: 180 }}>{label}</span>
      <span style={{ color: "#222", textAlign: "right", maxWidth: 260, wordBreak: "break-word" }}>{value}</span>
    </div>
  );
};

export default function PdfExtractor() {
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleFile = (e) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const extract = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const form = new FormData();
      form.append("file", file);
      const res = await fetch(`${API}/extract-pdf`, { method: "POST", body: form });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setResult(data.terms);
      setTimeline(data.timeline || []);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 style={{ fontFamily: "Fraunces, serif", fontWeight: 300, fontSize: 26, marginBottom: 4 }}>
        PDF Contract Extractor
      </h1>
      <p style={{ fontSize: 12, color: "#888", marginBottom: 24 }}>
        Upload a purchase agreement — Claude extracts all key terms and builds a deadline timeline.
      </p>

      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
        <label style={{
          fontSize: 12, padding: "8px 16px",
          background: "#fff", border: "0.5px solid #ddd",
          borderRadius: 8, cursor: "pointer",
          fontFamily: "DM Mono, monospace",
        }}>
          {file ? file.name : "choose PDF →"}
          <input type="file" accept=".pdf" onChange={handleFile} style={{ display: "none" }} />
        </label>
        <button
          onClick={extract}
          disabled={!file || loading}
          style={{
            fontSize: 12, padding: "8px 16px",
            background: !file || loading ? "#ccc" : "#1D9E75",
            color: "#fff", border: "none", borderRadius: 8,
            cursor: !file || loading ? "not-allowed" : "pointer",
            fontFamily: "DM Mono, monospace",
          }}
        >
          {loading ? "extracting…" : "→ extract with claude"}
        </button>
      </div>

      {error && (
        <div style={{ fontSize: 11, color: "#A32D2D", background: "#FCEBEB", padding: 10, borderRadius: 8, marginBottom: 16 }}>
          {error}
        </div>
      )}

      {result && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {/* Terms */}
          <div style={{ background: "#fff", border: "0.5px solid #e5e5e5", borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", letterSpacing: 0.8, marginBottom: 12 }}>
              Extracted terms
            </div>
            <Field label="Property" value={result.property_address} />
            <Field label="Purchase price" value={result.purchase_price} />
            <Field label="Earnest money" value={result.earnest_money} />
            <Field label="Closing date" value={result.closing_date} />
            <Field label="Buyer" value={result.buyer_name} />
            <Field label="Seller" value={result.seller_name} />
            <Field label="Buyer's agent" value={result.buyer_agent} />
            <Field label="Seller's agent" value={result.seller_agent} />
            <Field label="Title company" value={result.title_company} />
            <Field label="Lender" value={result.lender} />
            <Field label="Possession date" value={result.possession_date} />
            <Field label="Repair allowance" value={result.repair_allowance} />

            {result.special_conditions?.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", marginBottom: 6 }}>Special conditions</div>
                {result.special_conditions.map((s, i) => (
                  <div key={i} style={{ fontSize: 11, padding: "4px 8px", background: "#FAEEDA", color: "#854F0B", borderRadius: 4, marginBottom: 3 }}>{s}</div>
                ))}
              </div>
            )}

            {result.missing_fields?.length > 0 && (
              <div style={{ marginTop: 10 }}>
                <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", marginBottom: 6 }}>⚠ Unclear / missing</div>
                {result.missing_fields.map((f, i) => (
                  <div key={i} style={{ fontSize: 11, padding: "4px 8px", background: "#FCEBEB", color: "#A32D2D", borderRadius: 4, marginBottom: 3 }}>{f}</div>
                ))}
              </div>
            )}
          </div>

          {/* Timeline */}
          <div style={{ background: "#fff", border: "0.5px solid #e5e5e5", borderRadius: 12, padding: 16 }}>
            <div style={{ fontSize: 10, textTransform: "uppercase", color: "#999", letterSpacing: 0.8, marginBottom: 12 }}>
              Deadline timeline
            </div>
            {timeline.length === 0 ? (
              <div style={{ fontSize: 12, color: "#bbb" }}>No dates extracted</div>
            ) : (
              <div>
                {timeline.map((item, i) => (
                  <div key={i} style={{ display: "flex", gap: 12, paddingBottom: 12, position: "relative" }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flexShrink: 0 }}>
                      <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#1D9E75", marginTop: 2 }} />
                      {i < timeline.length - 1 && (
                        <div style={{ width: 1.5, flex: 1, background: "#e5e5e5", marginTop: 3 }} />
                      )}
                    </div>
                    <div style={{ paddingBottom: 4 }}>
                      <div style={{ fontSize: 12, fontWeight: 500 }}>{item.event}</div>
                      <div style={{ fontSize: 11, color: "#888", marginTop: 2 }}>{item.date}</div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
