import { useState } from "react";

function EmailDraft({ emailText }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(emailText || "");
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <section className="grid gap-3 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="text-base font-semibold text-slate-900">
        Generated Customer Communication (sent automatically via email)
      </h2>
      <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-slate-100 p-4 text-sm text-slate-700">
        {emailText || "No email draft available."}
      </pre>
      <button
        className="w-fit rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
        onClick={handleCopy}
        type="button"
      >
        {copied ? "Copied" : "Copy Email"}
      </button>
    </section>
  );
}

export default EmailDraft;
