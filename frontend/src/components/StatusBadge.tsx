import { cn } from "../utils/style";

const tones: Record<string, string> = {
  connected: "bg-mint text-spruce",
  active: "bg-mint text-spruce",
  completed: "bg-mint text-spruce",
  waiting: "bg-amber/10 text-amber",
  detected: "bg-emergency/10 text-emergency",
  low: "bg-amber/10 text-amber",
  moderate: "bg-aisoft text-ai",
  high: "bg-mint text-spruce"
};

export function StatusBadge({ value, label, className }: { value: string; label?: string; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-extrabold", tones[value] ?? "bg-ink/5 text-muted", className)}>
      <span className="status-dot" />
      {label ?? value}
    </span>
  );
}
