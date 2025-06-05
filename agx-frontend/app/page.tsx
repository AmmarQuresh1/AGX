"use client"; // If you're in the App Router

import { useState } from "react";

export default function Home() {
  const [prompt, setPrompt] = useState("");
  const [downloading, setDownloading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setDownloading(true);
    try {
      const response = await fetch("http://localhost:8000/", {
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
      if (!response.ok) throw new Error("Failed to get file.");
      // File download magic:
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "plan.py";
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      if (err instanceof Error) {
        alert(err.message);
      } else {
        alert("Failed to get file.");
      }
    }
    setDownloading(false);
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
      <h1 style={{ fontSize: "2.5rem", fontWeight: "bold", marginBottom: "2rem" }}>
        AGX Plan Generator
      </h1>
      <form onSubmit={handleSubmit} style={{ display: "flex", alignItems: "center" }}>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt"
          style={{
            width: 320,
            padding: 12,
            marginRight: 12,
            fontSize: "1.2rem",
            borderRadius: 6,
            border: "1px solid #888",
          }}
        />
        <button
          type="submit"
          disabled={downloading || !prompt}
          style={{
            padding: "12px 24px",
            fontSize: "1.2rem",
            borderRadius: 6,
            border: "2px solid #171717", // <-- Button border
            background: downloading ? "#eee" : "#fff",
            color: "#171717",
            cursor: downloading || !prompt ? "not-allowed" : "pointer",
            fontWeight: "bold",
          }}
        >
          {downloading ? "Generating..." : "Generate Plan"}
        </button>
      </form>
      <p style={{ marginTop: 24, color: "#444", fontSize: "1.1rem" }}>
        Five plans a day for now.
      </p>
    </main>
  );
}