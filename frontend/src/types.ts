export type Profile = {
  id: number;
  user_id: number;
  name: string;
  age: number | null;
  biological_sex: string | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: string;
  primary_goal: string;
  health_goals: string | null;
  known_conditions: string | null;
  injuries_or_limitations: string | null;
  dietary_preferences: string | null;
  created_at: string;
  updated_at: string;
};

export type CheckIn = {
  id: number;
  user_id: number;
  sleep_hours: number;
  sleep_quality: number;
  energy_level: number;
  stress_level: number;
  muscle_soreness: number;
  pain_or_discomfort?: string | null;
  planned_activity?: string | null;
  notes?: string | null;
  created_at: string;
};

export type RecommendationResult = {
  summary: string;
  readiness: { level: "low" | "moderate" | "high"; explanation: string };
  today_focus: string;
  movement: {
    title: string;
    recommendation: string;
    intensity: "low" | "moderate" | "high";
    duration: string;
    reasoning: string;
  };
  recovery: { recommendation: string; reasoning: string };
  nutrition: { recommendation: string; reasoning: string };
  sleep: { recommendation: string; reasoning: string };
  things_to_avoid: string[];
  important_notes: string[];
  medical_safety_message: string | null;
};

export type Recommendation = {
  id: number;
  user_id: number;
  checkin_id: number | null;
  recommendation_type: string;
  structured_result: RecommendationResult;
  created_at: string;
};

export type ECGAnalysis = {
  id: number;
  user_id: number;
  original_filename: string;
  status: string;
  document_summary: string;
  structured_result: {
    document_type: string;
    analysis_status: string;
    document_summary: string;
    detected_measurements: { name: string; value: string; source_page: number | null }[];
    observations: { title: string; description: string; importance: string; source_page: number | null }[];
    possible_patterns: { name: string; explanation: string; confidence: string }[];
    signal_or_document_quality: { level: string; explanation: string };
    recommended_next_steps: string[];
    questions_for_doctor: string[];
    urgent_flags: string[];
    limitations: string[];
  };
  created_at: string;
};

export type EmergencyContact = {
  id: number;
  user_id: number;
  name: string;
  relationship: string;
  telegram_chat_id: string | null;
  pairing_code: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Device = {
  id: number;
  user_id: number;
  name: string;
  device_id: string;
  status: string;
  last_seen_at: string | null;
  created_at: string;
  device_secret?: string;
};

export type FallIncident = {
  id: number;
  user_id: number;
  device_id: number | null;
  event_timestamp: string;
  confidence: number | null;
  sensor_payload: Record<string, unknown>;
  status: string;
  telegram_notification_status: string;
  created_at: string;
};
