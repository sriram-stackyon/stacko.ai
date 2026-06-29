import { useEffect, useState } from "react";

import { getClaimById, getClaims } from "../api/claims";
import ClaimResult from "../components/ClaimResult";
import ClaimsHistory from "../components/ClaimsHistory";
import EmailDraft from "../components/EmailDraft";
import LoadingSpinner from "../components/LoadingSpinner";

function HistoryPage() {
  const [claims, setClaims] = useState([]);
  const [selectedClaim, setSelectedClaim] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadClaims() {
      try {
        const data = await getClaims();
        setClaims(data);
      } catch (loadError) {
        setError(loadError?.response?.data?.detail || "Failed to load claims history.");
      } finally {
        setLoading(false);
      }
    }

    loadClaims();
  }, []);

  const handleSelect = async (claimId) => {
    try {
      const detail = await getClaimById(claimId);
      setSelectedClaim(detail);
    } catch (detailError) {
      setError(detailError?.response?.data?.detail || "Failed to load claim details.");
    }
  };

  if (loading) {
    return <LoadingSpinner message="Loading claims history..." />;
  }

  return (
    <div className="grid gap-6">
      <h2 className="text-xl font-semibold text-slate-900">Claims History</h2>

      {error ? <div className="rounded-md bg-red-100 px-4 py-3 text-sm text-red-700">{error}</div> : null}

      <ClaimsHistory claims={claims} onSelect={handleSelect} />

      {selectedClaim ? (
        <div className="grid gap-4">
          <ClaimResult claim={selectedClaim} />
          <EmailDraft emailText={selectedClaim.email_draft} />
        </div>
      ) : null}
    </div>
  );
}

export default HistoryPage;
