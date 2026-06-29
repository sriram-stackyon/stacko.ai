import { useState } from "react";

import { submitClaim } from "../api/claims";
import ClaimForm from "../components/ClaimForm";
import ClaimResult from "../components/ClaimResult";
import EmailDraft from "../components/EmailDraft";
import LoadingSpinner from "../components/LoadingSpinner";

const STEPS = [
  "Uploading photos...",
  "Verifying policy...",
  "Assessing damage...",
  "Running fraud checks...",
  "Generating claim decision...",
  "Drafting customer email...",
];

function SubmitClaimPage() {
  const [status, setStatus] = useState("idle");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [stepIndex, setStepIndex] = useState(0);

  const handleSubmit = async (formData) => {
    setStatus("loading");
    setError("");
    setResult(null);
    setStepIndex(0);

    const interval = setInterval(() => {
      setStepIndex((current) => (current + 1) % STEPS.length);
    }, 1400);

    try {
      const data = await submitClaim(formData);
      setResult(data);
      setStatus("result");
    } catch (submissionError) {
      setStatus("error");
      setError(submissionError?.response?.data?.detail || "Claim submission failed.");
    } finally {
      clearInterval(interval);
    }
  };

  return (
    <div className="grid gap-6">
      <ClaimForm isLoading={status === "loading"} onSubmit={handleSubmit} />

      {status === "loading" ? <LoadingSpinner message={STEPS[stepIndex]} /> : null}

      {status === "error" ? (
        <div className="rounded-md bg-red-100 px-4 py-3 text-sm font-medium text-red-700">{error}</div>
      ) : null}

      {status === "result" && result ? (
        <>
          <ClaimResult claim={result} />
          <EmailDraft emailText={result.email_draft} />
        </>
      ) : null}
    </div>
  );
}

export default SubmitClaimPage;
