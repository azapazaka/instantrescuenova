export function formatDate(value?: string) {
  const date = value ? new Date(value) : new Date();
  return new Intl.DateTimeFormat("ru-RU", { day: "numeric", month: "long", year: "numeric" }).format(date);
}

export function formatTime(value: string) {
  return new Intl.DateTimeFormat("ru-RU", { hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

export function completionPercent(profile?: {
  age: number | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: string;
  primary_goal: string;
  health_goals: string | null;
}) {
  if (!profile) return 0;
  const fields = [profile.age, profile.height_cm, profile.weight_kg, profile.activity_level, profile.primary_goal, profile.health_goals];
  return Math.round((fields.filter(Boolean).length / fields.length) * 100);
}
