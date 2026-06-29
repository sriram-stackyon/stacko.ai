function formatCurrency(value) {
  if (value === null || value === undefined) {
    return "No payout applicable";
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function badgeClass(value) {
  const normalized = (value || "").toLowerCase();
  if (normalized === "approved" || normalized === "low") {
    return "bg-green-100 text-green-800";
  }
  if (normalized === "denied" || normalized === "high") {
    return "bg-red-100 text-red-800";
  }
  return "bg-yellow-100 text-yellow-800";
}

function ClaimResult({ claim }) {
  if (!claim) {
    return null;
  }

  return (
    <section className="grid gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-center gap-3">
        <h2 className="text-lg font-semibold text-slate-900">Claim Result</h2>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ${badgeClass(claim.decision)}`}>
          {claim.decision || "Pending"}
        </span>
      </div>

      <div className="grid gap-3 rounded-lg border border-slate-200 bg-slate-50 p-4">
        <h3 className="text-sm font-semibold text-slate-700">Damage Assessment</h3>
        <p className="text-sm text-slate-700">{claim.damage_description || "No damage details"}</p>
        <div className="flex flex-wrap gap-3 text-sm">
          <span className="rounded bg-white px-3 py-1 text-slate-700">
            Estimated Cost: {formatCurrency(claim.estimated_repair_cost)}
          </span>
          <span className={`rounded px-3 py-1 font-semibold ${badgeClass(claim.damage_severity)}`}>
            Severity: {claim.damage_severity || "unknown"}
          </span>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <span className="text-sm font-medium text-slate-700">Fraud Risk</span>
        <span className={`rounded-full px-3 py-1 text-xs font-semibold uppercase ${badgeClass(claim.fraud_risk)}`}>
          {claim.fraud_risk || "unknown"}
        </span>
      </div>

      <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
        <h3 className="text-sm font-semibold text-slate-700">Payout</h3>
        <p className="mt-1 text-sm text-slate-800">{formatCurrency(claim.payout_amount)}</p>
      </div>

      <div className="w-full rounded-md bg-slate-100 p-4 text-sm text-slate-700">
        <p className="font-semibold text-slate-800">Decision Reason</p>
        <p className="mt-1">{claim.decision_reason || "No decision reason available."}</p>
      </div>
    </section>
  );
}

export default ClaimResult;
