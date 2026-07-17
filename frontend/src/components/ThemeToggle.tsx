import { Moon, Sun } from "lucide-react";

import { useTheme } from "../contexts/ThemeContext";
import { cn } from "../utils/style";

export function ThemeToggle({ className }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const dark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={cn(
        "group flex min-h-12 min-w-12 items-center justify-center rounded-lg border border-line bg-white px-2 text-ink transition hover:bg-mint/70",
        className
      )}
      aria-label={dark ? "Включить светлую тему" : "Включить темную тему"}
      title={dark ? "Светлая тема" : "Темная тема"}
    >
      {dark ? (
        <Sun className="h-5 w-5 text-amber transition group-hover:rotate-12" aria-hidden="true" />
      ) : (
        <Moon className="h-5 w-5 text-spruce transition group-hover:-rotate-12" aria-hidden="true" />
      )}
    </button>
  );
}
