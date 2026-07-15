export function LoadingProgress({ steps }: { steps: string[] }) {
  return (
    <div className="card rounded-lg p-5" role="status" aria-live="polite">
      <div className="mb-4 h-2 overflow-hidden rounded-full bg-line">
        <div className="h-full w-2/3 animate-pulse rounded-full bg-teal" />
      </div>
      <div className="space-y-2">
        {steps.map((step) => (
          <div key={step} className="flex items-center gap-3 text-sm font-bold text-muted">
            <span className="h-2 w-2 rounded-full bg-teal" />
            {step}
          </div>
        ))}
      </div>
    </div>
  );
}
