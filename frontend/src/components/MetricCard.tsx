import type { LucideIcon } from "lucide-react";

export function MetricCard({ icon: Icon, label, value, detail }: { icon: LucideIcon; label: string; value: string; detail?: string }) {
  return (
    <div className="rounded-lg border border-line bg-white/70 p-4">
      <div className="mb-3 flex h-10 w-10 items-center justify-center rounded-lg bg-mint text-spruce">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </div>
      <p className="text-sm font-bold text-muted">{label}</p>
      <p className="mt-1 text-2xl font-extrabold text-ink">{value}</p>
      {detail ? <p className="mt-1 text-xs font-semibold text-muted">{detail}</p> : null}
    </div>
  );
}
