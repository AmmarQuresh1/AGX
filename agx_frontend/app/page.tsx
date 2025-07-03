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
        throw new Error("Rate limit reached: 5 plans per day. Please try again tommorow.");
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
            AGX uses AI to generate structured JSON plans which are then statically validated against a pre-vetted function library before being compiled into production-ready code.
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
                placeholder="Enter your prompt"
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
                processingStep === 1 ? "[1/3] GENERATING JSON PLAN..." :
                processingStep === 2 ? "[2/3] VERIFYING PLAN AGAINST FUNCTION REGISTRY..." :
                "[3/3] COMPILING SECURE PYTHON SCRIPT..."
              ) : result}
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
            The Engine and The Roadmap
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
                AGX is a verifiable AI engine that translates your commands into reliable, production-ready workflows.
              </p>
              <p style={{ color: "#4b5563", lineHeight: 1.6, marginTop: 4, marginBottom: 4 }}>
                This live showcase demonstrates our core principle: <strong>From Prompt to Verified Plan.</strong>
                We are actively expanding the function registry to cover
                more clouds and services.
              </p>
              <ul style={{ paddingLeft: "1.25rem", listStyle: "disc" }}>
                <li style={{ marginBottom: "1rem" }}>
                  <strong>🛡️ Reliable by Design. No Hallucinations.</strong>
                  <p
                    style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                  >
                    Our <strong>verification engine</strong> validates every execution plan against a 
                    registry of approved functions before it runs, eliminating the random failures 
                    and unpredictable behaviour of typical AI agents.
                  </p>
                </li>
                <li style={{ marginBottom: "1rem" }}>
                  <strong>👀 Transparent & Auditable</strong>
                  <p
                    style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                  >
                    AGX generates a <strong>clean Python script</strong> for every task. You see
                    exactly what will happen, providing a clear and auditable
                    workflow every time.
                  </p>
                </li>
                <li>
                  <strong>⚙️ Built for Complex, Real-World Tasks</strong>
                  <p
                    style={{ margin: "0.25em 0", color: "#4b5563", lineHeight: 1.6 }}
                  >
                    With built-in <strong>dependency resolution</strong>, the engine can orchestrate
                    multi-step processes like building an image, deploying it, and
                    then monitoring the result.
                  </p>
                </li>
              </ul>
              
              <h4 style={{ marginTop: "1.5rem", marginBottom: "0.5rem", fontSize: "1.1rem", color: "#374151" }}>Available Tools:</h4>
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
            <div
              style={{
                flex: 1,
                borderLeft: "1px solid #e5e7eb",
                paddingLeft: "2rem",
                paddingRight: 10
              }}
            >
              <h3 style={{ marginTop: 0, fontSize: "1.3rem", fontWeight: 600 }}>The Future: The AGX CLI</h3>
              <p style={{ color: "#4b5563", lineHeight: 1.6, marginBottom: "1.5rem" }}>
                The next evolution of AGX is a powerful, context-aware CLI designed for professional DevOps workflows. It will bring the same verifiable engine to your local machine, with state management, file system access, and deep integrations with AWS, Kubernetes, and more.
              </p>
              
              <h4 style={{ marginTop: "1rem", marginBottom: "0.5rem", fontSize: "1.1rem", color: "#374151" }}>Coming Features:</h4>
              <ul style={{ paddingLeft: "1.25rem", listStyle: "disc", color: "#4b5563", lineHeight: 1.6 }}>
                <li style={{ marginBottom: "0.75rem" }}>
                  <strong>Local State Management</strong>
                  <p style={{ margin: "0.25em 0", color: "#6b7280", fontSize: "0.95em" }}>
                    Track deployments, resources, and configurations across your entire infrastructure.
                  </p>
                </li>
                <li style={{ marginBottom: "0.75rem" }}>
                  <strong>AWS Integration</strong>
                  <p style={{ margin: "0.25em 0", color: "#6b7280", fontSize: "0.95em" }}>
                    Deploy to EC2, Lambda, ECS, and manage RDS databases with natural language commands.
                  </p>
                </li>
                <li style={{ marginBottom: "0.75rem" }}>
                  <strong>Kubernetes Orchestration</strong>
                  <p style={{ margin: "0.25em 0", color: "#6b7280", fontSize: "0.95em" }}>
                    Generate and apply manifests, manage deployments, and scale workloads safely.
                  </p>
                </li>
                <li style={{ marginBottom: "0.75rem" }}>
                  <strong>GitHub Actions Integration</strong>
                  <p style={{ margin: "0.25em 0", color: "#6b7280", fontSize: "0.95em" }}>
                    Generate CI/CD pipelines that integrate seamlessly with your verification engine.
                  </p>
                </li>
              </ul>
              
              <div style={{ 
                background: "#f8fafc", 
                border: "1px solid #e2e8f0", 
                borderRadius: "8px", 
                padding: "1rem", 
                marginTop: "1.5rem" 
              }}>
                <p style={{ 
                  margin: 0, 
                  color: "#475569", 
                  fontSize: "0.95em", 
                  lineHeight: 1.5 
                }}>
                  <strong>Interested in the CLI?</strong> I'm developing it with feedback from real-world DevOps teams. 
                  Reach out to discuss your use case and get priority access to the beta.
                </p>
              </div>
            </div>
          </div>
        </div>
        {/*footer*/}
        <a href="https://www.linkedin.com/in/ammar-qureshi-083831274" style={{color: "#2779F6", marginTop: 30, fontSize: "1.1rem"}}>Built by Ammar Qureshi, founder of AGX</a>
        <p style={{ marginTop: 8, color: "#444", fontSize: "1.1rem", paddingBottom: "4rem", }}>
          Five plans a day for now.
        </p>
        <SpeedInsights />
        <Analytics />
      </main>
  );
}