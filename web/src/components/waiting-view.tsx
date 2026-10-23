"use client";

import { useEffect, useState } from "react";

const steps = ["Uploading video", "Extracting evidence", "Checking claims"];

export function WaitingView({ status }: { status: "queued" | "processing" }) {
  const [elapsed, setElapsed] = useState(0);
  useEffect(() => {
    const started = Date.now();
    const timer = window.setInterval(() => setElapsed(Math.floor((Date.now() - started) / 1000)), 1_000);
    return () => window.clearInterval(timer);
  }, []);
  const activeStep = status === "queued" ? 0 : 1;
  return <section className="waiting-view" aria-live="polite">
    <p className="eyebrow">Live analysis</p>
    <div className="waiting-spinner" aria-hidden="true" />
    <h1>{status === "queued" ? "Your demo is queued" : "Checking your evidence"}</h1>
    <p>{status === "queued" ? "A worker will start shortly." : "Usually complete in about 90 seconds."} {elapsed > 0 && `Elapsed ${elapsed}s.`}</p>
    <ol className="analysis-steps">{steps.map((step, index) => <li className={index <= activeStep ? "analysis-steps__active" : ""} key={step}>{step}</li>)}</ol>
  </section>;
}
