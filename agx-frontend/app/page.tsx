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
      alert("Something went wrong!");
    }
    setDownloading(false);
  };

  return (
    <main style={{ padding: "2rem" }}>
      <h1>AGX Plan Generator</h1>
      <form onSubmit={handleSubmit}>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Enter your prompt"
          style={{ width: 300, padding: 8, marginRight: 8 }}
        />
        <button type="submit" disabled={downloading || !prompt}>
          {downloading ? "Generating..." : "Generate Plan"}
        </button>
      </form>
    </main>
  );
}