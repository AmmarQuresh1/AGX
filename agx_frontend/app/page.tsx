"use client"; // If you're in the App Router

import { useState } from "react";
import { FiCopy } from "react-icons/fi";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { Analytics } from "@vercel/analytics/next";

function CLICard() {
  const [submitting, setSubmitting] = useState(false);
  const [notice, setNotice] = useState<{ type: "success" | "error"; text: string } | null>(null);

  // Set to true if you’re sending marketing emails to UK users (UK GDPR/PECR opt‑in).
  const REQUIRE_UK_OPT_IN = true;

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setNotice(null);

    const form = e.currentTarget;
    const data = new FormData(form);

    try {
      const res = await fetch("https://formspree.io/f/mwpnagok", {
        method: "POST",
        headers: { Accept: "application/json" },
        body: data,
      });

      if (res.ok) {
        form.reset();
        setNotice({ type: "success", text: "Thanks! I’ll send you an email." });
      } else {
        setNotice({ type: "error", text: "Sorry, couldn’t submit. Please email cli@agx.run." });
      }
    } catch {
      setNotice({ type: "error", text: "Network error. Please try again or email cli@agx.run." });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="mt-8 rounded-2xl card">
      <h3 className="text-sm font-semibold">AGX CLI (private alpha)</h3>
      <ul className="mt-2 list-disc pl-5 text-sm leading-6 text-subtle">
        <li>AWS-first: generates Terraform from validated plans</li>
        <li>Local-first: no freeform shell; registry-only</li>
        <li>Deterministic by design: static checks before codegen</li>
      </ul>

      <form onSubmit={handleSubmit} className="mt-3" style={{ display: "grid", gap: 8 }}>
        {/* honeypot to reduce spam */}
        <input type="text" name="_gotcha" style={{ display: "none" }} tabIndex={-1} autoComplete="off" />

        {/* required email—single field for simplicity */}
        <label className="text-sm text-subtle">
          Work email
          <input
            type="email"
            name="email"
            required
            placeholder="you@company.com"
            className="mt-1 w-full input"
          />
        </label>

        {/* optional UK marketing consent */}
        {REQUIRE_UK_OPT_IN && (
          <label className="flex items-start gap-2 text-sm text-subtle">
            <input type="checkbox" name="consent" required className="mt-1" />
            <span>I agree to receive emails about the AGX CLI private alpha.</span>
          </label>
        )}

        {/* context/segmentation */}
        <input type="hidden" name="source" value="agx.run_cli_card" />
        <input type="hidden" name="product" value="AGX CLI (private alpha)" />

    <button type="submit" disabled={submitting} className="rounded-md button" style={{ width: "fit-content", background: submitting ? "var(--accent)" : "var(--surface)" }}>
          {submitting ? "Submitting…" : "Join early list"}
        </button>

        {notice && (
          <p
            aria-live="polite"
            className="text-sm"
      style={{ color: notice.type === "success" ? "#0a7d3b" : "#b00020" }}
          >
            {notice.text}
          </p>
        )}
      </form>

    <p className="mt-2 text-xs text-muted">
        Prefer email?{" "}
        <a
          className="underline"
          href="mailto:cli@agx.run?subject=AGX%20CLI%20(private%20alpha)%20%E2%80%94%20early%20access&body=Hi%20Ammar,%0A%0AMy%20AWS%20stack%3A%0AInfra%20to%20automate%3A%0ATerraform%20workflow%3A%0A%0AThanks!"
        >
          cli@agx.run
        </a>
      </p>
    </div>
  );
}

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [downloading, setDownloading] = useState(false);
  const [result, setResult] = useState("")
  const [copied, setCopied] = useState(false);
  const [processingStep, setProcessingStep] = useState(0);
  const MIN_SPINNER_MS = 6000; // Wait ~6s total before showing results

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
    
  // Wait for at least MIN_SPINNER_MS total before showing results
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
  }, MIN_SPINNER_MS);
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
    <main className="main">
      <div className="container">
        {/* The logo is now in a div, not an H1. */}
        <div style={{ margin: 0, fontWeight: 'normal', fontSize: '1rem' }}>
          <img
            src="/resources/agx_white.png"
            alt="AGX: The Verifiable AI Workflow Engine for DevOps"
            className="logo-img"
          />
        </div>

        {/* Hero Section */}
        <div className="hero">
          {/* This is now the single, correct H1 for the page */}
          <h1 className="hero-title">
            From Prompt to Verified DevOps Automation
          </h1>
          <p className="hero-lead">
            AGX generates structured JSON plans, validates them against a pre‑vetted function library, then compiles them into executable code.
          </p>
          <p className="hero-sub">
            Live demo: natural‑language prompt → JSON plan → validator check → compiled script.
          </p>
          <button
            onClick={() => {
              const toolSection = document.getElementById('tool-section');
              if (toolSection) {
                toolSection.scrollIntoView({ behavior: 'smooth' });
              }
            }}
            className="cta-btn"
          >
            Try the Live Showcase
          </button>
        </div>

        {/* Tool Section */}
        <div id="tool-section">
          <h2 className="sm:nowrap" style={{ marginBottom: 24, fontSize: "clamp(1.5rem, 4vw, 2.5rem)" }}>
            Describe what you want to automate...
          </h2>

          {/* Responsive form container */}
          <div className="prompt-form-container" style={{ width: "100%", maxWidth: "90%", margin: "0 auto" }}>
            <form onSubmit={handleSubmit} className="prompt-form" style={{ marginTop: 8, justifyContent: "center" }}>
              <input
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder={'e.g., "Create an S3 bucket named agx-demo-123 with all public access blocked and save to main.tf"'}
                className="prompt-input input"
                style={{ padding: 12, fontSize: "1.2rem" }}
              />
              <button
                type="submit"
                disabled={downloading || !prompt}
                className="prompt-btn button"
                style={{ padding: "12px 24px", fontSize: "1.2rem", whiteSpace: "nowrap", background: downloading ? "var(--accent)" : "var(--surface)" }}
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
              className="pre-box"
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
              className={`copy-btn ${copied ? 'copied' : ''}`}
              style={{ opacity: result ? 1 : 0.5, pointerEvents: result ? 'auto' : 'none' }}
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
            className="button"
            style={{ padding: "12px 24px", fontSize: "1.2rem", width: "100%", background: !result ? "var(--surface)" : "var(--accent)", color: !result ? "#999" : "#000" }}
          >
            Download Script
          </button>
          </div>
        </div>

        {/* New parent container for centering and constraining width */}
  <div style={{ maxWidth: "1024px", margin: "0 auto", padding: "0 1rem", marginTop: 16 }}>
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
        display: "flex",
            }}
          >
            {/* Left Column: About the Showcase Engine */}
            <div style={{ flex: 1.5, paddingLeft: 10 }}>
              <h3 style={{ marginTop: 0, fontSize: "1.3rem", fontWeight: 600 }}>About the Showcase Engine</h3>
              <p className="text-subtle" style={{ lineHeight: 1.6 }}>
                AGX is a verifiable AI engine that translates your commands into reliable, executable workflows.
              </p>
              <p className="text-subtle" style={{ lineHeight: 1.6, marginTop: 4, marginBottom: 4 }}>
                This live showcase demonstrates our core principle: <strong>From Prompt to Verified Plan.</strong>
              </p>
              <br />
              <ul style={{ paddingLeft: "1.25rem", listStyle: "disc" }}>
                <li style={{ marginBottom: "1rem" }}>
                  <strong>Reliable by design. Hallucination‑resistant.</strong>
          <p className="text-subtle" style={{ margin: "0.25em 0", lineHeight: 1.6 }}>
                    Our <strong>verification engine</strong> validates every execution plan against a
                    registry of approved functions before it runs, preventing unapproved actions and
                    reducing the unpredictable behaviour of typical AI agents.
                  </p>
                </li>
                <li style={{ marginBottom: "1rem" }}>
                  <strong>Transparent & auditable</strong>
          <p className="text-subtle" style={{ margin: "0.25em 0", lineHeight: 1.6 }}>
                    AGX generates a <strong>clean Python script</strong> for every task. You see
                    exactly what will happen, providing a clear and auditable
                    workflow every time.
                  </p>
                </li>
                <li>
                  <strong>Built for real workflows</strong>
          <p className="text-subtle" style={{ margin: "0.25em 0", lineHeight: 1.6 }}>
                    With built-in <strong>dependency resolution</strong>, the engine can orchestrate
                    multi-step processes like building an image, deploying it, and
                    then monitoring the result.
                  </p>
                </li>
              </ul>
              
        <h4 style={{ marginTop: "1.5rem", marginBottom: "0.5rem", fontSize: "1.1rem" }} className="text-subtle">Available tools (demo subset):</h4>
        <ul style={{ paddingLeft: "1.25rem", listStyle: "disc", lineHeight: 1.6 }} className="text-subtle">
                <li style={{ marginBottom: "0.25rem" }}><code>set_bucket_name</code> — set name for reuse</li>
                <li style={{ marginBottom: "0.25rem" }}><code>create_aws_s3_bucket</code> — emit bucket HCL</li>
                <li style={{ marginBottom: "0.25rem" }}><code>aws_s3_bucket_public_access_block</code> — block public access</li>
                <li style={{ marginBottom: "0.25rem" }}><code>save_hcl_to_file</code> — write main.tf</li>
              </ul>
        <p className="text-subtle" style={{ lineHeight: 1.6, marginTop: "1rem" }}>
                Try chaining them together in your prompt! Here's a sample:{" "}
                <code
                  style={{
                    backgroundColor: "#f3f4f6",
                    padding: "0.2rem 0.4rem",
                    borderRadius: "4px",
                    fontSize: "0.9em",
                  }}
                >
                  Create an S3 bucket named agx-demo-123 with all public access blocked and save to main.tf.
                </code>
              </p>
            </div>
            {/* Right Column: The Future */}
            <div style={{ flex: 1, paddingLeft: 20 }}>
              <CLICard />
            </div>
          </div>
        </div>
        {/*footer*/}
    <p className="footer-blurb">
          You can generate up to five plans per day
        </p>
    <a href="https://www.linkedin.com/in/ammar-qureshi-083831274" style={{color: "#2779F6", fontSize: "1.1rem"}}>Built by Ammar Qureshi, founder of AGX (linkedin)</a>
    <p className="footer-line">
          AGX™ is a product of AQ DIGITAL LIMITED <br/>
          In the UK, AGX is offered under the mark AQ DIGITAL AGX™
        </p>
        <SpeedInsights />
        <Analytics />
      </main>
  );
}