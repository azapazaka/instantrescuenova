import type { LucideIcon } from "lucide-react";

export function EmptyState({ icon: Icon, title, text }: { icon: LucideIcon; title: string; text: string }) {
  return (
    <div className="rounded-lg border border-dashed border-line bg-white/55 p-6 text-center">
      <Icon className="mx-auto mb-3 h-8 w-8 text-teal" aria-hidden="true" />
      <p className="font-extrabold text-ink">{title}</p>
      <p className="mt-1 text-sm leading-6 text-muted">{text}</p>
    </div>
  );
}
