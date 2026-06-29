function formatCurrency(value) {
  if (value === null || value === undefined) {
    return "-";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function decisionBadge(decision) {
  const normalized = (decision || "").toLowerCase();
  if (normalized === "approved") {
    return "bg-green-100 text-green-800";
  }
  if (normalized === "denied") {
    return "bg-red-100 text-red-800";
  }
  return "bg-yellow-100 text-yellow-800";
}

function ClaimsHistory({ claims, onSelect }) {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-sm">
      <table className="min-w-full text-left text-sm">
        <thead className="bg-slate-100 text-slate-700">
          <tr>
            <th className="px-4 py-3 font-semibold">Policy #</th>
            <th className="px-4 py-3 font-semibold">Claimant</th>
            <th className="px-4 py-3 font-semibold">Incident Type</th>
            <th className="px-4 py-3 font-semibold">Decision</th>
            <th className="px-4 py-3 font-semibold">Payout</th>
            <th className="px-4 py-3 font-semibold">Date</th>
          </tr>
        </thead>
        <tbody>
          {claims.map((claim) => (
            <tr
              key={claim.id}
              className="cursor-pointer border-t border-slate-200 hover:bg-slate-50"
              onClick={() => onSelect(claim.id)}
            >
              <td className="px-4 py-3">{claim.policy_number}</td>
              <td className="px-4 py-3">{claim.claimant_name}</td>
              <td className="px-4 py-3 capitalize">{claim.incident_type}</td>
              <td className="px-4 py-3">
                <span className={`rounded-full px-2 py-1 text-xs font-semibold uppercase ${decisionBadge(claim.decision)}`}>
                  {claim.decision || "pending"}
                </span>
              </td>
              <td className="px-4 py-3">{formatCurrency(claim.payout_amount)}</td>
              <td className="px-4 py-3">{new Date(claim.created_at).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default ClaimsHistory;
