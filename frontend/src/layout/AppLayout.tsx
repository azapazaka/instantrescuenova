import { Activity, FileText, HeartPulse, Home, LogOut, ShieldCheck, UserRound } from "lucide-react";
import { useState } from "react";
import { NavLink, Outlet } from "react-router-dom";

import { BrandIcon } from "../components/BrandIcon";
import { ThemeToggle } from "../components/ThemeToggle";
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
    <div className="min-h-screen pb-28 lg:pb-0 lg:pl-72">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-72 flex-col border-r border-line bg-white/95 px-4 py-5 shadow-calm backdrop-blur lg:flex">
        <NavLink to="/" className="flex items-center gap-3 rounded-2xl px-2 py-2">
          <BrandIcon className="h-12 w-12 rounded-xl" />
          <div className="min-w-0">
            <span className="block truncate font-display text-xl font-semibold text-ink">
              Instant Rescue
            </span>
            <span className="block truncate text-xs font-bold uppercase tracking-wide text-teal">
              Пульс и безопасность
            </span>
          </div>
        </NavLink>

        <nav className="mt-8 flex flex-1 flex-col gap-2" aria-label="Основная навигация">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={to === "/"}
              className={({ isActive }) =>
                `flex min-h-12 items-center gap-3 rounded-xl px-3 text-base font-extrabold transition ${
                  isActive
                    ? "bg-spruce text-white shadow-calm"
                    : "text-muted hover:bg-ink/5 hover:text-ink"
                }`
              }
            >
              <Icon className="h-5 w-5" aria-hidden="true" />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="space-y-3 border-t border-line pt-4">
          <ThemeToggle className="w-full justify-start gap-3 rounded-xl px-3" />

          <div className="relative">
            <button
              type="button"
              onClick={() => setMenuOpen((open) => !open)}
              className="flex min-h-12 w-full items-center gap-3 rounded-xl border border-line bg-white px-3 font-extrabold text-ink"
              aria-expanded={menuOpen}
              aria-haspopup="menu"
              aria-label="Аккаунт"
            >
              <UserRound className="h-5 w-5 shrink-0 text-teal" aria-hidden="true" />
              <span className="min-w-0 flex-1 truncate text-left text-sm">{email}</span>
            </button>

            {menuOpen ? (
              <>
                <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} aria-hidden="true" />
                <div
                  role="menu"
                  className="absolute bottom-full left-0 z-20 mb-2 w-full rounded-xl border border-line bg-white p-2 shadow-calm"
                >
                  <p className="truncate px-3 py-2 text-sm text-muted">{email}</p>
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
      </aside>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>

      <p className="mx-auto max-w-7xl px-4 pb-4 text-center text-sm text-muted sm:px-6 lg:px-8">
        Instant Rescue не ставит диагноз и не заменяет врача.
      </p>

      <div className="fixed inset-x-0 bottom-0 z-30 border-t border-line bg-white/95 shadow-calm backdrop-blur lg:hidden">
        <div className="mx-auto grid max-w-7xl grid-cols-[1fr_auto] items-center gap-1 px-1 py-1 sm:px-3">
          <nav className="grid min-w-0 grid-cols-5 gap-1" aria-label="Основная навигация">
            {nav.map(({ to, label, shortLabel, icon: Icon }) => (
              <NavLink
                key={to}
                to={to}
                end={to === "/"}
                aria-label={label}
                className={({ isActive }) =>
                  `flex min-h-14 min-w-0 flex-col items-center justify-center gap-1 rounded-lg px-1 text-[11px] font-extrabold transition ${
                    isActive ? "bg-mint text-spruce" : "text-muted hover:bg-ink/5 hover:text-ink"
                  }`
                }
              >
                <Icon className="h-6 w-6" aria-hidden="true" />
                <span className="truncate">{shortLabel}</span>
              </NavLink>
            ))}
          </nav>

          <div className="flex shrink-0 items-center gap-1">
            <ThemeToggle className="min-h-14" />

            <div className="relative">
              <button
                type="button"
                onClick={() => setMenuOpen((open) => !open)}
                className="flex min-h-14 min-w-12 items-center justify-center rounded-lg border border-line bg-white px-2 font-extrabold text-ink"
                aria-expanded={menuOpen}
                aria-haspopup="menu"
                aria-label="Аккаунт"
              >
                <UserRound className="h-6 w-6 text-teal" aria-hidden="true" />
              </button>

              {menuOpen ? (
                <>
                  <div className="fixed inset-0 z-10" onClick={() => setMenuOpen(false)} aria-hidden="true" />
                  <div
                    role="menu"
                    className="absolute bottom-full right-0 z-20 mb-2 w-60 rounded-xl border border-line bg-white p-2 shadow-calm"
                  >
                    <p className="truncate px-3 py-2 text-sm text-muted">{email}</p>
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
        </div>
      </div>
    </div>
  );
}
