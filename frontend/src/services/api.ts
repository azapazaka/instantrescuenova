import type {
  CheckIn,
  Device,
  ECGAnalysis,
  EmergencyContact,
  FallIncident,
  Profile,
  Recommendation
} from "../types";

const API_BASE = "";

type ApiErrorShape = {
  error?: {
    code: string;
    message: string;
  };
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers }
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiErrorShape;
    throw new Error(body.error?.message ?? "Сервер временно недоступен.");
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; ai_mode: string; app_env: string }>("/api/health"),
  getProfile: () => request<Profile>("/api/profile"),
  updateProfile: (profile: Partial<Profile>) => request<Profile>("/api/profile", { method: "PUT", body: JSON.stringify(profile) }),
  createCheckIn: (payload: Omit<CheckIn, "id" | "user_id" | "created_at">) =>
    request<CheckIn>("/api/checkins", { method: "POST", body: JSON.stringify(payload) }),
  listCheckIns: () => request<CheckIn[]>("/api/checkins"),
  createRecommendation: (checkinId?: number) =>
    request<Recommendation>("/api/recommendations", { method: "POST", body: JSON.stringify({ checkin_id: checkinId ?? null }) }),
  listRecommendations: () => request<Recommendation[]>("/api/recommendations"),
  createECGAnalysis: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<ECGAnalysis>("/api/ecg-analyses", { method: "POST", body: form });
  },
  listECGAnalyses: () => request<ECGAnalysis[]>("/api/ecg-analyses"),
  listContacts: () => request<EmergencyContact[]>("/api/emergency-contacts"),
  addContact: (payload: { name: string; relationship: string; telegram_username: string }) =>
    request<EmergencyContact>("/api/emergency-contacts", { method: "POST", body: JSON.stringify(payload) }),
  deleteContact: (id: number) => request<{ ok: boolean; message: string }>(`/api/emergency-contacts/${id}`, { method: "DELETE" }),
  testContact: (id: number) => request<{ ok: boolean; message: string }>(`/api/emergency-contacts/${id}/test`, { method: "POST" }),
  regeneratePairing: (id: number) =>
    request<EmergencyContact>(`/api/emergency-contacts/${id}/regenerate-pairing`, { method: "POST" }),
  listDevices: () => request<Device[]>("/api/devices"),
  addDevice: (name: string) => request<Device>("/api/devices", { method: "POST", body: JSON.stringify({ name }) }),
  listIncidents: () => request<FallIncident[]>("/api/fall-incidents"),
  simulateFall: () => request<FallIncident>("/api/demo/simulate-fall", { method: "POST" })
};
