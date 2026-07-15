import type { ReactNode } from "react";

export function PageHeader({ title, eyebrow, children }: { title: string; eyebrow?: string; children?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div>
        {eyebrow ? <p className="mb-2 text-sm font-extrabold uppercase tracking-wide text-teal">{eyebrow}</p> : null}
        <h1 className="font-display text-4xl font-semibold leading-tight text-ink md:text-5xl">{title}</h1>
      </div>
      {children}
    </header>
  );
}
