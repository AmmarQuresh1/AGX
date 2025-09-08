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
  const [processingStep, setProcessingStep] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault(); // Stops reload
    setDownloading(true);
    setResult(""); // Clear previous result
    setProcessingStep(1);
    
    let apiResponse: any = null;
    let apiError: any = null;
    
    // Start the API call immediately but don't wait for it
    const apiCall = fetch("/api", { 
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ prompt }),
    }).then(async (response) => {
      if (response.status == 429) {
        throw new Error("Rate limit reached: 5 plans per day. Please try again tomorrow.");
      }
      if (!response.ok) throw new Error("Failed to get code.");
      
      const code = await response.text();
      return code;
    }).then((code) => {
      apiResponse = code;
    }).catch((err) => {
      apiError = err;
    });
    
    // Show processing steps with guaranteed delays
    setTimeout(() => setProcessingStep(2), 2000);  // 2 seconds for step 1
    setTimeout(() => setProcessingStep(3), 4000);  // 4 seconds total (2 more for step 2)
    
    // Wait for at least 9 seconds total before showing results
    setTimeout(async () => {
      // Ensure API call is complete
      await apiCall;
      
      if (apiError) {
        if (apiError.message.includes("Rate limit")) {
          alert(apiError.message);
        } else if (apiError instanceof Error) {
          alert(apiError.message);
        } else {
          alert("Failed to get code.");
        }
        setProcessingStep(0);
        setDownloading(false);
        return;
      }
      
      if (apiResponse) {
        setResult(apiResponse);
      }
      
      setProcessingStep(0); // Reset processing step
      setDownloading(false);
    }, 6000);
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
        {/* The logo is now in a div, not an H1. */}
        <div style={{ margin: 0, fontWeight: 'normal', fontSize: '1rem' }}>
          <img
            src="/resources/agx_white.png"
            // Bonus: Improved alt text for SEO and accessibility
            alt="AGX: The Verifiable AI Workflow Engine for DevOps"
            style={{
               height: 40,
               display: 'block', // Good practice for images in blocks
               marginBottom: 32
            }}
          />
        </div>

        {/* Hero Section */}
        <div style={{ 
          textAlign: "center", 
          minHeight: "60vh", 
          display: "flex", 
          flexDirection: "column", 
          justifyContent: "center", 
          alignItems: "center",
          marginBottom: 64 
        }}>
          {/* This is now the single, correct H1 for the page */}
          <h1 style={{ 
            fontSize: "3rem", 
            fontWeight: 700, 
            marginBottom: 32, 
            lineHeight: 1.1,
            margin: "0 0 32px 0"
          }}>
            From Prompt to Verified DevOps Automation
          </h1>
          <p style={{ 
            fontSize: "1.3rem", 
            color: "#4b5563", 
            marginBottom: 48, 
            lineHeight: 1.5,
            maxWidth: 600,
            margin: "0 auto 48px auto"
          }}>
            AGX generates structured JSON plans, validates them against a pre‑vetted function library, then compiles them into executable code.
          </p>
          <p style={{ 
            fontSize: "1.1rem", 
            color: "#6b7280", 
            marginTop: -24,
            marginBottom: 48, 
            lineHeight: 1.5,
            maxWidth: 600,
            margin: "0 auto 48px auto"
          }}>
            Live demo: natural‑language prompt → JSON plan → validator check → compiled script.
          </p>
          <button
            onClick={() => {
              const toolSection = document.getElementById('tool-section');
              if (toolSection) {
                toolSection.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            style={{
              padding: "16px 32px",
              fontSize: "1.3rem",
              borderRadius: 6,
              border: "1px solid #b3b2ae",
              background: "#E0DBD1",
              color: "black",
              cursor: "pointer",
              fontWeight: 600,
              marginBottom: 32
            }}
          >
            Try the Live Showcase
          </button>
        </div>

        {/* Tool Section */}
        <div id="tool-section">
          <h2 style={{ marginBottom: 24 }}>
            Describe what you want to automate...
          </h2>

          {/* Responsive form container */}
          <div className="prompt-form-container" style={{ width: "100%", maxWidth: "90%", margin: "0 auto" }}>
            <form onSubmit={handleSubmit} className="prompt-form" style={{ 
              display: "flex", 
              marginTop: 8,
              justifyContent: "center",
              width: "100%",
              gap: 12,
            }}>
              <input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={'e.g., "Create a Dockerfile for a FastAPI app on port 8000 and deploy to Fly.io"'}
                className="prompt-input"
                style={{
                  flex: 1,
                  padding: 12,
                  fontSize: "1.2rem",
                  borderRadius: 6,
                  background: "#fffefe",
                  border: "1px solid #b3b2ae",
                  minWidth: 0, // Prevents overflow in flex
                }}
              />
              <button
                type="submit"
                disabled={downloading || !prompt}
                className="prompt-btn"
                style={{
                  padding: "12px 24px",
                  fontSize: "1.2rem",
                  borderRadius: 6,
                  border: "1px solid #b3b2ae",
                  background: downloading ? "#E0DBD1" : "#faf8f4",
                  color: "#000000",
                  cursor: downloading || !prompt ? "not-allowed" : "pointer",
                  fontWeight: "normal",
                  whiteSpace: "nowrap",
                }}
              >
                {downloading ? "Generating..." : "Generate Script"}
              </button>
            </form>
          </div>

          <h2 style={{ marginTop: 32, marginBottom: 8, fontSize: "2rem" }}>
          Output
          </h2>
          {/* PREFORMATTED BOX */}
          <div style={{ position: "relative", width: "100%", marginBottom: 16 }}>
            <pre
              role="status"
              aria-live="polite"
              aria-busy={downloading ? "true" : "false"}
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
              {downloading && processingStep > 0 ? (
                processingStep === 1 ? "[1/3] Generating JSON plan…" :
                processingStep === 2 ? "[2/3] Validating plan against function registry…" :
                "[3/3] Compiling verified Python script…"
              ) : result}
            </pre>
            <button
              type="button"
              title={copied ? "Copied!" : "Copy to clipboard"}
              aria-label="Copy output to clipboard"
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
            title={!result ? "Generate a script first" : "Download the generated script"}
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
        </div>

        {/* New parent container for centering and constraining width */}
        <div
          style={{
            maxWidth: "1024px",
            margin: "0 auto",
            padding: "0 1rem",
            marginTop: 16
          }}
        >
          <h2 style={{
            textAlign: "center",
            marginBottom: 32,
            marginTop: 48
          }}>
            About the Engine
          </h2>
          
          {/* Responsive two-column container */}
          <div
            className="roadmap-container"
            style={{
              maxWidth: 1000,
              fontFamily: "sans-serif",
              borderTop: "1px solid #e5e7eb",
              marginTop: "2rem",
              paddingTop: "2rem",
              gap: "2rem",
            }}
          >
            {/* Left Column: About the Showcase Engine */}
            <div style={{ flex: 1.5, paddingLeft: 10 }}>
              <h3 style={{ marginTop: 0, fontSize: "1.3rem", fontWeight: 600 }}>About the Showcase Engine</h3>
              <p style={{ color: "#4b5563", lineHeight: 1.6 }}>
                AGX is a verifiable AI engine that translates your commands into reliable, executable workflows.
              </p>
              <p style={{ color: "#4b5563", lineHeight: 1.6, marginTop: 4, marginBottom: 4 }}>
                This live showcase demonstrates our core principle: <strong>From Prompt to Verified Plan.</strong>
              </p>
              <br />
              <ul style={{ paddingLeft: "1.25rem", listStyle: "disc" }}>
                <li style={{ marginBottom: "1rem" }}>
                  <strong>Reliable by design. Hallucination‑resistant.</strong>
                  <p
                    style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                  >
                    Our <strong>verification engine</strong> validates every execution plan against a
                    registry of approved functions before it runs, preventing unapproved actions and
                    reducing the unpredictable behaviour of typical AI agents.
                  </p>
                </li>
                <li style={{ marginBottom: "1rem" }}>
                  <strong>Transparent & auditable</strong>
                  <p
                    style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                  >
                    AGX generates a <strong>clean Python script</strong> for every task. You see
                    exactly what will happen, providing a clear and auditable
                    workflow every time.
                  </p>
                </li>
                <li>
                  <strong>Built for real workflows</strong>
                  <p
                    style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                  >
                    With built-in <strong>dependency resolution</strong>, the engine can orchestrate
                    multi-step processes like building an image, deploying it, and
                    then monitoring the result.
                  </p>
                </li>
              </ul>
              
              <h4 style={{ marginTop: "1.5rem", marginBottom: "0.5rem", fontSize: "1.1rem", color: "#374151" }}>Available tools (demo subset):</h4>
              <ul style={{ paddingLeft: "1.25rem", listStyle: "disc", color: "#4b5563", lineHeight: 1.6 }}>
                <li style={{ marginBottom: "0.25rem" }}><code>check_docker_status</code>: Checks if Docker is running.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>build_docker_image</code>: Builds a Docker image.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>create_dockerfile</code>: Generates a Dockerfile.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>deploy_to_fly</code>: Deploys an application to Fly.io.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>scale_fly_app</code>: Scales a Fly.io application.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>get_app_status</code>: Gets the status of a Fly.io app.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>monitor_deployment</code>: Monitors a Fly.io deployment.</li>
                <li style={{ marginBottom: "0.25rem" }}><code>cleanup_resources</code>: Cleans up Fly.io and Docker resources.</li>
              </ul>
              <p style={{ color: "#4b5563", lineHeight: 1.6, marginTop: "1rem" }}>
                Try chaining them together in your prompt! Here's a sample:{" "}
                <code
                  style={{
                    backgroundColor: "#f3f4f6",
                    padding: "0.2rem 0.4rem",
                    borderRadius: "4px",
                    fontSize: "0.9em",
                  }}
                >
                  Create a Dockerfile for a Python FastAPI application on port 8000, build the image, and then deploy it to Fly.io.
                </code>
              </p>
            </div>

            {/* Right Column: The Future */}
          </div>
        </div>
        {/*footer*/}
        <a href="https://www.linkedin.com/in/ammar-qureshi-083831274" style={{color: "#2779F6", marginTop: 30, fontSize: "1.1rem"}}>Built by Ammar Qureshi, founder of AGX</a>
        <p style={{ marginTop: 8, color: "#444", fontSize: "1.1rem", paddingBottom: "4rem", }}>
          You can generate up to five plans per day.
        </p>
        <SpeedInsights />
        <Analytics />
      </main>
  );
}