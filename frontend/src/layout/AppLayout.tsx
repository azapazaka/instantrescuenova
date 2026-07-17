import { Activity, FileText, HeartPulse, Home, LogOut, ShieldCheck, UserRound } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../contexts/AuthContext";

// shortLabel keeps the 5-up mobile bar readable — "Безопасность" overflows a
// 75px column at 375px, and truncating it mid-word helps nobody.
const nav = [
  { to: "/", label: "Главная", shortLabel: "Главная", icon: Home },
  { to: "/heart-rate", label: "Пульс", shortLabel: "Пульс", icon: HeartPulse },
  { to: "/documents", label: "Анализы", shortLabel: "Анализы", icon: FileText },
  { to: "/recommendations", label: "План дня", shortLabel: "План", icon: Activity },
  { to: "/safety", label: "Безопасность", shortLabel: "Помощь", icon: ShieldCheck }
];

export function AppLayout() {
  const { session, signOut } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const email = session?.user.email ?? "";

  return (
    <div className="min-h-screen pb-24 lg:pb-0">
      <header className="sticky top-0 z-30 border-b border-line bg-shell/90 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-4 px-4 sm:px-6 lg:h-20 lg:px-8">
          <NavLink to="/" className="flex shrink-0 items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-spruce text-white">
              <HeartPulse className="h-6 w-6" />
            </div>
            <span className="font-display text-2xl font-semibold text-ink">Instant Rescue</span>
          </NavLink>

          {/* Desktop navigation. On mobile this collapses to the bottom bar. */}
          <nav className="hidden items-center gap-1 lg:flex" aria-label="Основная навигация">
            {nav.map(({ to, label, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                className={({ isActive }) =>
                  `flex min-h-12 items-center gap-2 rounded-xl px-4 text-base font-extrabold transition ${
                    isActive ? "bg-spruce text-white" : "text-muted hover:bg-ink/5 hover:text-ink"
                  }`
                }
              >
                <Icon className="h-5 w-5" aria-hidden="true" />
                {label}
              </NavLink>
            ))}
          </nav>

          <div className="relative shrink-0">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              className="flex min-h-12 items-center gap-2 rounded-xl border border-line bg-white px-3 font-extrabold text-ink"
              aria-expanded={menuOpen}
              aria-haspopup="menu"
            >
              <UserRound className="h-5 w-5 text-teal" aria-hidden="true" />
              <span className="hidden max-w-40 truncate text-sm sm:inline">{email}</span>
            </button>

            {menuOpen ? (
              <>
                {/* Click-away layer, so the menu closes without a global listener. */}
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} aria-hidden="true" />
                <div
                  role="menu"
                  className="absolute right-0 z-20 mt-2 w-60 rounded-xl border border-line bg-white p-2 shadow-calm"
                >
                  <p className="truncate px-3 py-2 text-sm text-muted sm:hidden">{email}</p>
                  <NavLink
                    to="/profile"
                    role="menuitem"
                    onClick={() => setMenuOpen(false)}
                    className="flex min-h-12 items-center gap-3 rounded-lg px-3 font-extrabold text-ink hover:bg-ink/5"
                  >
                    <UserRound className="h-5 w-5 text-teal" aria-hidden="true" />
                    Профиль
                  </NavLink>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={signOut}
                    className="flex min-h-12 w-full items-center gap-3 rounded-lg px-3 font-extrabold text-emergency hover:bg-emergency/5"
                  >
                    <LogOut className="h-5 w-5" aria-hidden="true" />
                    Выйти
                  </button>
                </div>
              </>
            ) : null}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>

      <p className="mx-auto max-w-7xl px-4 pb-4 text-center text-sm text-muted sm:px-6 lg:px-8">
        Instant Rescue не ставит диагноз и не заменяет врача.
      </p>

      {/* No horizontal padding: five columns already consume the full 375px on
          the narrowest phones, and padding pushed the grid past the viewport. */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-30 grid grid-cols-5 border-t border-line bg-white/95 py-1 shadow-calm backdrop-blur lg:hidden"
        aria-label="Мобильная навигация"
      >
        {nav.map(({ to, label, shortLabel, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            aria-label={label}
            className={({ isActive }) =>
              `flex min-h-14 min-w-0 flex-col items-center justify-center gap-1 rounded-lg text-[11px] font-extrabold ${
                isActive ? "bg-mint text-spruce" : "text-muted"
              }`
            }
          >
            <Icon className="h-6 w-6" aria-hidden="true" />
            {shortLabel}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
