"use client"; // If you're in the App Router

import { useState } from "react";
import { FiCopy } from "react-icons/fi";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState("")
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Stops reload
    setDownloading(true);
    try {
      const response = await fetch("/api", { // http://localhost:8000/
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ prompt }),
      });
      if (response.status == 429) {
        alert("Rate limit reached: 5 plans per day. Please try again tommorow.")
        setDownloading(false);
        return;
      }
      if (!response.ok) throw new Error("Failed to get code.");

      // Get code:
      const code = await response.text();
      setResult(code);

    } catch (err) {
      if (err instanceof Error) {
        alert(err.message);
      } else {
        alert("Failed to get code.");
      }
    }
    setDownloading(false);
  };

  const handleDownload = () => {
    if (!result) {
      alert("No code to download. Generate a script first!");
      return;
    }
    
    const blob = new Blob([result], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "plan.py";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  };

  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "flex-start",
        paddingTop: "4rem",
        background: "var(--background)",
        color: "var(--foreground)",
      }}
    >
      <div
        style={{
          width: 700,
          maxWidth: "90vw",
          margin: "0 auto",
          textAlign: "left", 
          alignItems: "center"
        }}
      >
        <img
          src="/resources/agx_white.png"
          alt="AGX Logo"
          style={{
             height: 40, 
             textAlign: "left",
             marginBottom: 32
             }}
        />

        <h2 style={{ marginBottom: 24 }}>
          Describe what you want to automate...
        </h2>

        <form onSubmit={handleSubmit} style={{ 
          display: "flex", 
          marginTop: 8,
          justifyContent: "center",
          width: "100%",
          }}>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt"
          style={{
            flex: 1,
            padding: 12,
            marginRight: 12,
            fontSize: "1.2rem",
            borderRadius: 6,
            background: "#fffefe",
            border: "1px solid #b3b2ae",
          }}
        />
        <button
          type="submit"
          disabled={downloading || !prompt}
          style={{
            padding: "12px 24px",
            fontSize: "1.2rem",
            borderRadius: 6,
            border: "1px solid #b3b2ae", // <-- Button border
            background: downloading ? "#E0DBD1" : "#faf8f4",
            color: "#000000",
            cursor: downloading || !prompt ? "not-allowed" : "pointer",
            fontWeight: "normal",
          }}
        >
          {downloading ? "Generating..." : "Generate Script"}
        </button>
        </form>

        <h2 style={{ marginTop: 32, marginBottom: 8 }}>
        Output
        </h2>
        {/* PREFORMATTED BOX */}
        <div style={{ position: "relative", width: "100%" }}>
          <pre
            style={{
              background: "#f9f8f5",
              padding: 16,
              borderRadius: 6,
              width: "100%",
              minHeight: 120,
              maxHeight: 400,
              paddingBottom: 16,
              overflowX: "auto",
              fontSize: "1rem",
              color: "#222",
              border: "1px solid #b3b2ae",
              textAlign: "left",
              boxSizing: "border-box",
            }}
          >
            {result}
          </pre>
          <button
            type="button"
            onClick={() => {
              if (result) {
                navigator.clipboard.writeText(result);
                setCopied(true);
                setTimeout(() => setCopied(false), 800);
              }
            }}
            style={{
              position: "absolute",
              top: 12,
              right: 12,
              padding: "6px 14px",
              fontSize: "1rem",
              borderRadius: 4,
              border: "1px solid #b3b2ae",
              background: copied ? "#E0DBD1" : "#f9f8f5",
              color: "#222",
              cursor: "pointer",
              opacity: result ? 1 : 0.5,
              pointerEvents: result ? "auto" : "none",
            }}
            disabled={!result}
          >
            <FiCopy size={20} />
          </button>
        </div>
        <button
          type="button"
          onClick={handleDownload}
          disabled={!result}
          style={{
            padding: "12px 24px",
            fontSize: "1.2rem",
            borderRadius: 6,
            marginTop: 16,
            border: "1px solid #b3b2ae",
            background: !result ? "#faf8f5" : "#E0DBD1",
            color: !result ? "#999" : "#000000",
            cursor: !result ? "not-allowed" : "pointer",
            fontWeight: "normal",
            width: "100%",
          }}
        >
          Download Script
        </button>

      </div>

      <p style={{ marginTop: 24, color: "#444", fontSize: "1.1rem" }}>
        Five plans a day for now.
      </p>
    </main>
  );
}