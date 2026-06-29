function LoadingSpinner({ message = "Processing claim..." }) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-slate-200 bg-white p-10 shadow-sm">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-200 border-t-brand-600" />
      <p className="text-sm font-medium text-slate-600">{message}</p>
    </div>
  );
}

export default LoadingSpinner;
