import { useState } from "react";

const INCIDENT_TYPES = [
  { label: "Collision", value: "collision" },
  { label: "Third-Party", value: "third-party" },
  { label: "Theft", value: "theft" },
  { label: "Fire", value: "fire" },
  { label: "Weather", value: "weather" },
  { label: "Vandalism", value: "vandalism" },
];

function ClaimForm({ onSubmit, isLoading }) {
  const [policyNumber, setPolicyNumber] = useState("");
  const [claimantName, setClaimantName] = useState("");
  const [claimantEmail, setClaimantEmail] = useState("");
  const [incidentType, setIncidentType] = useState("collision");
  const [incidentDescription, setIncidentDescription] = useState("");
  const [photos, setPhotos] = useState([]);
  const [error, setError] = useState("");

  const handleFileChange = (event) => {
    const selected = Array.from(event.target.files || []);
    if (selected.length > 3) {
      setError("You can upload up to 3 photos only.");
      setPhotos([]);
      return;
    }
    setError("");
    setPhotos(selected);
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    const formData = new FormData();
    formData.append("policy_number", policyNumber.trim());
    formData.append("claimant_name", claimantName.trim());
    formData.append("claimant_email", claimantEmail.trim());
    formData.append("incident_type", incidentType);
    formData.append("incident_description", incidentDescription.trim());
    photos.forEach((photo) => formData.append("photos", photo));
    onSubmit(formData);
  };

  return (
    <form className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm" onSubmit={handleSubmit}>
      <h2 className="text-lg font-semibold text-slate-900">Submit a Claim</h2>

      <label className="grid gap-1 text-sm text-slate-700">
        Policy Number
        <input
          className="rounded-md border border-slate-300 px-3 py-2 outline-none ring-brand-600 transition focus:ring-2"
          required
          type="text"
          value={policyNumber}
          onChange={(event) => setPolicyNumber(event.target.value)}
        />
      </label>

      <label className="grid gap-1 text-sm text-slate-700">
        Claimant Name
        <input
          className="rounded-md border border-slate-300 px-3 py-2 outline-none ring-brand-600 transition focus:ring-2"
          required
          type="text"
          value={claimantName}
          onChange={(event) => setClaimantName(event.target.value)}
        />
      </label>

      <label className="grid gap-1 text-sm text-slate-700">
        Claimant Email
        <input
          className="rounded-md border border-slate-300 px-3 py-2 outline-none ring-brand-600 transition focus:ring-2"
          required
          type="email"
          value={claimantEmail}
          onChange={(event) => setClaimantEmail(event.target.value)}
        />
      </label>

      <label className="grid gap-1 text-sm text-slate-700">
        Incident Type
        <select
          className="rounded-md border border-slate-300 px-3 py-2 outline-none ring-brand-600 transition focus:ring-2"
          required
          value={incidentType}
          onChange={(event) => setIncidentType(event.target.value)}
        >
          {INCIDENT_TYPES.map((type) => (
            <option key={type.value} value={type.value}>
              {type.label}
            </option>
          ))}
        </select>
      </label>

      <label className="grid gap-1 text-sm text-slate-700">
        Incident Description
        <textarea
          className="min-h-28 rounded-md border border-slate-300 px-3 py-2 outline-none ring-brand-600 transition focus:ring-2"
          required
          value={incidentDescription}
          onChange={(event) => setIncidentDescription(event.target.value)}
        />
      </label>

      <label className="grid gap-1 text-sm text-slate-700">
        Photo Upload
        <input
          accept="image/*"
          className="rounded-md border border-slate-300 px-3 py-2"
          multiple
          type="file"
          onChange={handleFileChange}
        />
        <span className="text-xs text-slate-500">Up to 3 photos (JPG, PNG, WEBP).</span>
      </label>

      {error ? <div className="rounded-md bg-red-100 px-3 py-2 text-sm text-red-700">{error}</div> : null}

      <button
        className="rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isLoading}
        type="submit"
      >
        {isLoading ? "Submitting..." : "Submit Claim"}
      </button>
    </form>
  );
}

export default ClaimForm;
