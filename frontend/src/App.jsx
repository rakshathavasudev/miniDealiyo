import { useState } from "react";
import EmailParser from "./components/EmailParser";
import DealHealthCard from "./components/DealHealthCard";
import PdfExtractor from "./components/PdfExtractor";

const TABS = ["Email Parser", "Deal Health", "PDF Extractor"];

export default function App() {
  const [tab, setTab] = useState(0);

  return (
    <div style={{ minHeight: "100vh", background: "#f8f7f4", fontFamily: "DM Mono, monospace" }}>
      {/* Header */}
      <header style={{
        borderBottom: "0.5px solid #ddd",
        background: "#fff",
        padding: "0 2rem",
        display: "flex",
        alignItems: "center",
        gap: "2rem",
        height: "52px",
      }}>
        <span style={{ fontFamily: "Fraunces, serif", fontWeight: 600, fontSize: 18, letterSpacing: -0.5 }}>
          Mini<em style={{ color: "#1D9E75" }}>Dealyo</em>
        </span>
        <nav style={{ display: "flex", gap: 0 }}>
          {TABS.map((t, i) => (
            <button
              key={t}
              onClick={() => setTab(i)}
              style={{
                fontSize: 12,
                padding: "0 14px",
                height: 52,
                background: "none",
                border: "none",
                borderBottom: tab === i ? "2px solid #1D9E75" : "2px solid transparent",
                color: tab === i ? "#1D9E75" : "#888",
                cursor: "pointer",
                fontFamily: "DM Mono, monospace",
                fontWeight: tab === i ? 500 : 400,
              }}
            >
              {t}
            </button>
          ))}
        </nav>
        <span style={{
          marginLeft: "auto", fontSize: 10,
          background: "#E1F5EE", color: "#0F6E56",
          padding: "3px 10px", borderRadius: 99,
        }}>
          powered by claude-sonnet-4
        </span>
      </header>

      {/* Content */}
      <main style={{ maxWidth: 860, margin: "0 auto", padding: "2rem 1.5rem" }}>
        {tab === 0 && <EmailParser />}
        {tab === 1 && <DealHealthCard />}
        {tab === 2 && <PdfExtractor />}
      </main>
    </div>
  );
}
