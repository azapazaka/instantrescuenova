import darkIcon from "../assets/brand-icon-dark.png";
import lightIcon from "../assets/brand-icon-light.png";
import { useTheme } from "../contexts/ThemeContext";
import { cn } from "../utils/style";

export function BrandIcon({ className }: { className?: string }) {
  const { theme } = useTheme();
  const dark = theme === "dark";

  return (
    <span
      className={cn(
        "relative inline-flex shrink-0 overflow-hidden rounded-2xl border border-line bg-white shadow-calm",
        className
      )}
      aria-hidden="true"
    >
      <img
        src={lightIcon}
        alt=""
        className={cn(
          "absolute inset-0 h-full w-full object-cover transition duration-500 ease-out",
          dark ? "scale-105 opacity-0" : "scale-100 opacity-100"
        )}
      />
      <img
        src={darkIcon}
        alt=""
        className={cn(
          "absolute inset-0 h-full w-full object-cover transition duration-500 ease-out",
          dark ? "scale-100 opacity-100" : "scale-95 opacity-0"
        )}
      />
    </span>
  );
}
