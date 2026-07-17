import { LogIn } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { BrandIcon } from "../components/BrandIcon";
import { ThemeToggle } from "../components/ThemeToggle";
import { useAuth } from "../contexts/AuthContext";
import { supabase } from "../services/supabase";

export function SignInPage() {
  const { session, loading } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  if (!loading && session) return <Navigate to="/" replace />;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setBusy(false);

    if (error) {
      toast.error(
        error.message === "Invalid login credentials"
          ? "Неверная почта или пароль."
          : error.message
      );
      return;
    }
    navigate("/", { replace: true });
  }

  return (
    <>
      <ThemeToggle className="fixed right-4 top-4 z-20" />
      <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-5 py-10">
        <div className="mb-8 text-center">
          <BrandIcon className="mx-auto mb-4 h-20 w-20" />
          <h1 className="font-display text-4xl font-semibold text-ink">Instant Rescue</h1>
          <p className="mt-3 text-lg leading-7 text-muted">
            Наблюдение за пульсом и помощь близких рядом.
          </p>
        </div>

        <form onSubmit={onSubmit} className="card rounded-2xl p-6">
          <label className="field-label" htmlFor="email">
            Электронная почта
          </label>
          <input
            id="email"
            type="email"
            className="field mb-5 text-lg"
            autoComplete="email"
            required
            value={email}
            onChange={(event) => setEmail(event.target.value)}
          />

          <label className="field-label" htmlFor="password">
            Пароль
          </label>
          <input
            id="password"
            type="password"
            className="field mb-6 text-lg"
            autoComplete="current-password"
            required
            value={password}
            onChange={(event) => setPassword(event.target.value)}
          />

          <button type="submit" className="btn btn-primary w-full text-lg" disabled={busy}>
            <LogIn className="h-5 w-5" />
            {busy ? "Входим…" : "Войти"}
          </button>
        </form>

        <p className="mt-6 text-center text-base text-muted">
          Нет аккаунта?{" "}
          <Link to="/signup" className="font-extrabold text-teal underline underline-offset-4">
            Зарегистрироваться
          </Link>
        </p>
      </main>
    </>
  );
}
