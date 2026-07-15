import { Activity, FileText, HeartPulse, Home, ShieldCheck, UserRound } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const nav = [
  { to: "/", label: "Главная", icon: Home },
  { to: "/recommendations", label: "План дня", icon: Activity },
  { to: "/ecg", label: "ЭКГ", icon: FileText },
  { to: "/safety", label: "Безопасность", icon: ShieldCheck },
  { to: "/profile", label: "Профиль", icon: UserRound }
];

export function AppLayout() {
  return (
    <div className="min-h-screen pb-20 lg:pb-0">
      <aside className="fixed left-0 top-0 hidden h-screen w-72 border-r border-line bg-ink px-5 py-6 text-white lg:block">
        <div className="mb-10 flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-mint text-spruce">
            <HeartPulse className="h-6 w-6" />
          </div>
          <div>
            <p className="font-display text-2xl font-semibold">Caspian Care</p>
          </div>
        </div>
        <nav className="space-y-2" aria-label="Основная навигация">
          {nav.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded-lg px-4 py-3 text-sm font-extrabold transition ${
                  isActive ? "bg-white text-ink" : "text-white/70 hover:bg-white/10 hover:text-white"
                }`
              }
            >
              <Icon className="h-5 w-5" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="absolute bottom-6 left-5 right-5 rounded-lg border border-white/10 bg-white/5 p-4 text-sm leading-6 text-white/70">
          Не является медицинским диагнозом.
        </div>
      </aside>

      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:ml-72 lg:px-8">
        <Outlet />
      </main>

      <nav className="fixed bottom-0 left-0 right-0 z-20 grid grid-cols-5 border-t border-line bg-white/95 px-2 py-2 shadow-calm backdrop-blur lg:hidden" aria-label="Мобильная навигация">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex flex-col items-center gap-1 rounded-lg px-1 py-2 text-[11px] font-extrabold ${isActive ? "bg-mint text-spruce" : "text-muted"}`
            }
          >
            <Icon className="h-5 w-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
