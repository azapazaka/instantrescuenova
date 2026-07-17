import { AlertTriangle, CheckCircle2, Eye, ShieldAlert } from "lucide-react";

import type { Severity } from "../types";
import { cn } from "../utils/style";

/**
 * Severity is never communicated by colour alone: each level carries its own
 * icon and word. Elderly users are the target audience here, and colour-blindness
 * plus low-contrast phone screens make a colour-only signal unreadable.
 */
const config: Record<Severity, { label: string; className: string; icon: typeof CheckCircle2 }> = {
  normal: { label: "Норма", className: "bg-mint text-spruce", icon: CheckCircle2 },
  watch: { label: "Наблюдаем", className: "bg-aisoft text-ai", icon: Eye },
  elevated: { label: "Отклонение", className: "bg-amber/15 text-amber", icon: AlertTriangle },
  high: { label: "Сильное отклонение", className: "bg-emergency/10 text-emergency", icon: ShieldAlert }
};

export function SeverityBadge({ severity, className }: { severity: Severity; className?: string }) {
  const { label, className: tone, icon: Icon } = config[severity] ?? config.normal;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-extrabold",
        tone,
        className
      )}
    >
      <Icon className="h-4 w-4" aria-hidden="true" />
      {label}
    </span>
  );
}
