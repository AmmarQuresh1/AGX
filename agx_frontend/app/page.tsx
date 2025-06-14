"use client"; // If you're in the App Router

import { useState } from "react";
import { FiCopy } from "react-icons/fi";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { Analytics } from "@vercel/analytics/next";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState("")
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Stops reload
    setDownloading(true);
    try {
      const response = await fetch("/api", { 
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
        <div style={{ position: "relative", width: "100%", marginBottom: 16 }}>
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

      {/* New parent container for centering and constraining width */}
      <div
        style={{
          maxWidth: "1024px", // Adjust this value to match your app's main content width
          margin: "0 auto",    // This is the magic for centering a block element
          padding: "0 1rem",   // Adds some space on the sides for smaller screens
          marginTop: 16
        }}
      >
        {/* Your existing two-column flex container */}
        <div
          style={{
            display: "flex",
            maxWidth: 1000,
            fontFamily: "sans-serif",
            borderTop: "1px solid #e5e7eb",
            marginTop: "2rem",
            paddingTop: "2rem",
            gap: "2rem",
          }}
        >
          {/* Left Column: What is AGX? */}
          <div style={{ flex: 1.5, paddingLeft: 10 }}>
            <h3 style={{ marginTop: 0, fontSize: "1.25rem" }}>What is AGX?</h3>
            <p style={{ color: "#4b5563", lineHeight: 1.6 }}>
              AGX is a deterministic AI engine that translates your commands into
              reliable, production-ready workflows.
            </p>
            <p style={{ color: "#4b5563", lineHeight: 1.6, marginTop: 4, marginBottom: 4 }}>
              This live showcase demonstrates our powerful "Zero to Deploy"
              capability. We are actively expanding the function registry to cover
              more clouds and services.
            </p>
            <ul style={{ paddingLeft: "1.25rem", listStyle: "disc" }}>
              <li style={{ marginBottom: "1rem" }}>
                <strong>Zero Hallucinations. Guaranteed.</strong>
                <p
                  style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                >
                  Our verification engine validates every execution plan before it
                  runs, eliminating the random failures and unpredictable behavior
                  of AI agents.
                </p>
              </li>
              <li style={{ marginBottom: "1rem" }}>
                <strong>Transparent & Auditable</strong>
                <p
                  style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                >
                  AGX generates a clean Python script for every task. You see
                  exactly what will happen, providing a clear and auditable
                  workflow every time.
                </p>
              </li>
              <li>
                <strong>Built for Complex, Real-World Tasks</strong>
                <p
                  style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                >
                  Our engine understands dependencies, allowing it to orchestrate
                  multi-step processes like building an image, deploying it, and
                  then monitoring the result.
                </p>
              </li>
            </ul>
          </div>

          {/* Right Column: How do I use it? */}
          <div
            style={{
              flex: 1,
              borderLeft: "1px solid #e5e7eb",
              paddingLeft: "2rem",
              paddingRight: 10
            }}
          >
            <h3 style={{ marginTop: 0, fontSize: "1.25rem" }}>How do I use it?</h3>
            <p style={{ color: "#4b5563", lineHeight: 1.6 }}>
              The AGX engine can currently use the following tools to build a plan.
              Try chaining them together in your prompt!
              <br />
              Here's a sample:{" "}
              <code
                style={{
                  backgroundColor: "#f3f4f6",
                  padding: "0.2rem 0.4rem",
                  borderRadius: "4px",
                  fontSize: "0.9em",
                }}
              >
                Create a Dockerfile for a Python FastAPI application
              </code>
            </p>
            <ul style={{ paddingLeft: 0, listStyle: "none" }}>
              {/* ... The rest of your list items ... */}
            </ul>
            <p
              style={{
                color: "#4b5563",
                lineHeight: 1.6,
                marginTop: "1.5rem",
              }}
            >
              <strong>Coming Soon:</strong> A powerful <strong>AGX CLI</strong> for full local
              integration, plus deeper support for AWS, Kubernetes, GitHub Actions, and more.
            </p>
          </div>
        </div>
      </div>
      <p style={{ marginTop: 24, color: "#444", fontSize: "1.1rem" }}>
        Five plans a day for now.
      </p>
      <SpeedInsights />
      <Analytics />
    </main>
  );
}