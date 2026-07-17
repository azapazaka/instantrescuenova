import { HeartPulse, UserPlus } from "lucide-react";
import { useState, type FormEvent } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { toast } from "sonner";

import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";
import { supabase } from "../services/supabase";

export function SignUpPage() {
  const { session, loading } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    relativeName: "",
    relativeRelationship: "Родственник",
    relativeTelegram: ""
  });
  const [busy, setBusy] = useState(false);

  if (!loading && session) return <Navigate to="/" replace />;

  function update(key: keyof typeof form) {
    return (event: { target: { value: string } }) =>
      setForm((prev) => ({ ...prev, [key]: event.target.value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (form.password.length < 8) {
      toast.error("Пароль должен быть не короче 8 символов.");
      return;
    }
    setBusy(true);

    const { data, error } = await supabase.auth.signUp({
      email: form.email,
      password: form.password
    });

    if (error) {
      setBusy(false);
      toast.error(error.message);
      return;
    }

    // Email confirmation may be on, in which case there is no session yet and we
    // cannot call our API. Say so plainly instead of failing silently.
    if (!data.session) {
      setBusy(false);
      toast.success("Аккаунт создан. Подтвердите почту и войдите.");
      navigate("/signin", { replace: true });
      return;
    }

    // Profile and emergency contact are created through our own API so they land
    // under the verified user id, not whatever the client claims.
    try {
      await api.updateProfile({
        name: form.name,
        activity_level: "Moderate",
        primary_goal: "Здоровье сердца"
      });

      if (form.relativeName && form.relativeTelegram) {
        await api.addContact({
          name: form.relativeName,
          relationship: form.relativeRelationship,
          telegram_username: form.relativeTelegram.startsWith("@")
            ? form.relativeTelegram
            : `@${form.relativeTelegram}`
        });
      }
    } catch {
      // The account exists; a failed contact insert must not strand the user on
      // the signup screen. They can add the contact from the Safety page.
      toast.message("Аккаунт создан. Контакт можно добавить на странице «Безопасность».");
    }

    setBusy(false);
    navigate("/", { replace: true });
  }

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-md flex-col justify-center px-5 py-10">
      <div className="mb-7 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-spruce text-white">
          <HeartPulse className="h-9 w-9" />
        </div>
        <h1 className="font-display text-4xl font-semibold text-ink">Регистрация</h1>
      </div>

      <form onSubmit={onSubmit} className="card rounded-2xl p-6">
        <label className="field-label" htmlFor="name">
          Как вас зовут
        </label>
        <input id="name" className="field mb-5 text-lg" required value={form.name} onChange={update("name")} />

        <label className="field-label" htmlFor="email">
          Электронная почта
        </label>
        <input
          id="email"
          type="email"
          className="field mb-5 text-lg"
          autoComplete="email"
          required
          value={form.email}
          onChange={update("email")}
        />

        <label className="field-label" htmlFor="password">
          Пароль
        </label>
        <input
          id="password"
          type="password"
          className="field text-lg"
          autoComplete="new-password"
          required
          minLength={8}
          value={form.password}
          onChange={update("password")}
        />
        <p className="mb-6 mt-2 text-sm text-muted">Не короче 8 символов.</p>

        <div className="mb-5 rounded-xl border border-line bg-mint/40 p-4">
          <p className="font-extrabold text-spruce">Близкий человек</p>
          <p className="mt-1 text-sm leading-6 text-muted">
            Ему придёт уведомление в Telegram, если система заметит падение. Это можно
            изменить позже.
          </p>
        </div>

        <label className="field-label" htmlFor="relativeName">
          Имя близкого
        </label>
        <input
          id="relativeName"
          className="field mb-5 text-lg"
          value={form.relativeName}
          onChange={update("relativeName")}
        />

        <label className="field-label" htmlFor="relativeRelationship">
          Кем приходится
        </label>
        <select
          id="relativeRelationship"
          className="field mb-5 text-lg"
          value={form.relativeRelationship}
          onChange={update("relativeRelationship")}
        >
          <option>Родственник</option>
          <option>Сын</option>
          <option>Дочь</option>
          <option>Супруг(а)</option>
          <option>Внук(чка)</option>
          <option>Сосед</option>
          <option>Опекун</option>
        </select>

        <label className="field-label" htmlFor="relativeTelegram">
          Telegram близкого
        </label>
        <input
          id="relativeTelegram"
          className="field text-lg"
          placeholder="@username"
          value={form.relativeTelegram}
          onChange={update("relativeTelegram")}
        />
        <p className="mb-6 mt-2 text-sm text-muted">
          После регистрации мы покажем код, который он отправит нашему боту.
        </p>

        <button type="submit" className="btn btn-primary w-full text-lg" disabled={busy}>
          <UserPlus className="h-5 w-5" />
          {busy ? "Создаём…" : "Создать аккаунт"}
        </button>
      </form>

      <p className="mt-6 text-center text-base text-muted">
        Уже есть аккаунт?{" "}
        <Link to="/signin" className="font-extrabold text-teal underline underline-offset-4">
          Войти
        </Link>
      </p>
    </main>
  );
}
