import type {
  CheckIn,
  Device,
  EmergencyContact,
  FallIncident,
  HealthDocument,
  HeartRateAnomaly,
  HeartRateLive,
  HeartRateReading,
  HeartRateSummary,
  Profile,
  Recommendation,
  ScenarioInfo
} from "../types";

const API_BASE = "";

type ApiErrorShape = {
  error?: {
    code: string;
    message: string;
  };
};

/** Set by AuthProvider. Always reads the live session, never a cached token. */
let accessTokenGetter: () => Promise<string | null> = async () => null;

export function setAccessTokenGetter(getter: () => Promise<string | null>) {
  accessTokenGetter = getter;
}

export class ApiError extends Error {
  constructor(message: string, readonly code: string, readonly status: number) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = await accessTokenGetter();
  const isFormData = init?.body instanceof FormData;

  const headers: Record<string, string> = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...((init?.headers as Record<string, string>) ?? {})
  };
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorShape;
    throw new ApiError(
      body.error?.message ?? "Сервер временно недоступен.",
      body.error?.code ?? "UNKNOWN",
      response.status
    );
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () =>
    request<{
      status: string;
      ai_mode: string;
      app_env: string;
      telegram_bot_username: string;
      telegram_configured: boolean;
    }>("/api/health"),

  getProfile: () => request<Profile>("/api/profile"),
  updateProfile: (profile: Partial<Profile>) =>
    request<Profile>("/api/profile", { method: "PUT", body: JSON.stringify(profile) }),

  createCheckIn: (payload: Omit<CheckIn, "id" | "user_id" | "created_at">) =>
    request<CheckIn>("/api/checkins", { method: "POST", body: JSON.stringify(payload) }),
  listCheckIns: () => request<CheckIn[]>("/api/checkins"),

  createRecommendation: (checkinId?: number) =>
    request<Recommendation>("/api/recommendations", {
      method: "POST",
      body: JSON.stringify({ checkin_id: checkinId ?? null })
    }),
  listRecommendations: () => request<Recommendation[]>("/api/recommendations"),

  // Heart rate
  liveHeartRate: () => request<HeartRateLive>("/api/heart-rate/live"),
  heartRateHistory: (hours = 6) => request<HeartRateReading[]>(`/api/heart-rate?hours=${hours}`),
  heartRateSummary: (hours = 24) => request<HeartRateSummary>(`/api/heart-rate/summary?hours=${hours}`),
  heartRateAnomalies: (limit = 20) => request<HeartRateAnomaly[]>(`/api/heart-rate/anomalies?limit=${limit}`),
  getScenario: () => request<ScenarioInfo>("/api/heart-rate/scenario"),
  setScenario: (scenario: string) =>
    request<ScenarioInfo>("/api/heart-rate/scenario", {
      method: "POST",
      body: JSON.stringify({ scenario })
    }),

  // Documents
  createDocumentAnalysis: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<HealthDocument>("/api/health-documents", { method: "POST", body: form });
  },
  listDocumentAnalyses: () => request<HealthDocument[]>("/api/health-documents"),

  // Safety
  listContacts: () => request<EmergencyContact[]>("/api/emergency-contacts"),
  addContact: (payload: { name: string; relationship: string; telegram_username?: string }) =>
    request<EmergencyContact>("/api/emergency-contacts", { method: "POST", body: JSON.stringify(payload) }),
  deleteContact: (id: number) =>
    request<{ ok: boolean; message: string }>(`/api/emergency-contacts/${id}`, { method: "DELETE" }),
  testContact: (id: number) =>
    request<{ ok: boolean; message: string }>(`/api/emergency-contacts/${id}/test`, { method: "POST" }),
  regeneratePairing: (id: number) =>
    request<EmergencyContact>(`/api/emergency-contacts/${id}/regenerate-pairing`, { method: "POST" }),

  listDevices: () => request<Device[]>("/api/devices"),
  addDevice: (name: string) => request<Device>("/api/devices", { method: "POST", body: JSON.stringify({ name }) }),
  listIncidents: () => request<FallIncident[]>("/api/fall-incidents"),
  simulateFall: () => request<FallIncident>("/api/demo/simulate-fall", { method: "POST" })
};
