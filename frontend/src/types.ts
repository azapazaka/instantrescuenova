export type Source = {
  title: string;
  org: string;
  url: string;
  year: number | null;
  section: string | null;
  quote?: string | null;
};

/** One feature's share of an anomaly score. This is what the UI explains with. */
export type FeatureContribution = {
  feature: string;
  label: string;
  value: number;
  baseline: number | null;
  deviation: number;
  weight: number;
  direction: "above" | "below" | "normal";
  explanation: string;
};

export type Profile = {
  id: number;
  user_id: string;
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
  resting_hr_baseline: number | null;
  created_at: string;
  updated_at: string;
};

export type CheckIn = {
  id: number;
  user_id: string;
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

export type Severity = "normal" | "watch" | "elevated" | "high";

export type HeartRateInsight = {
  summary: string;
  severity: Severity;
  average_bpm: number | null;
  resting_bpm: number | null;
  contributions: FeatureContribution[];
};

export type RecommendationBlock = {
  recommendation: string;
  reasoning: string;
  sources: Source[];
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
    sources: Source[];
  };
  recovery: RecommendationBlock;
  nutrition: RecommendationBlock;
  sleep: RecommendationBlock;
  things_to_avoid: string[];
  important_notes: string[];
  medical_safety_message: string | null;
  heart_rate_insight: HeartRateInsight | null;
};

export type Recommendation = {
  id: number;
  user_id: string;
  checkin_id: number | null;
  recommendation_type: string;
  structured_result: RecommendationResult;
  sources: Source[];
  ai_mode: string;
  created_at: string;
};

export type LifestyleAdvice = {
  recommendation: string;
  reasoning: string;
  sources: Source[];
};

export type HealthDocumentResult = {
  document_type: string;
  analysis_status: "completed" | "limited";
  document_summary: string;
  detected_measurements: {
    name: string;
    value: string;
    reference_range: string | null;
    status: "normal" | "borderline" | "out_of_range" | "unknown";
    source_page: number | null;
  }[];
  observations: {
    title: string;
    description: string;
    importance: "low" | "moderate" | "high";
    source_page: number | null;
  }[];
  nutrition_advice: LifestyleAdvice[];
  activity_advice: LifestyleAdvice[];
  document_quality: { level: "poor" | "fair" | "good"; explanation: string };
  recommended_next_steps: string[];
  questions_for_doctor: string[];
  urgent_flags: string[];
  limitations: string[];
};

export type HealthDocument = {
  id: number;
  user_id: string;
  original_filename: string;
  status: string;
  document_summary: string;
  structured_result: HealthDocumentResult;
  sources: Source[];
  ai_mode: string;
  created_at: string;
};

export type HeartRateReading = {
  id: number;
  user_id: string;
  bpm: number;
  source: string;
  context: string | null;
  measured_at: string;
};

export type HeartRateAnomaly = {
  id: number;
  user_id: string;
  window_start: string;
  window_end: string;
  anomaly_score: number;
  severity: Severity;
  predicted_label: string | null;
  rate_flag: string | null;
  baseline_source: string;
  features: Record<string, number>;
  contributions: FeatureContribution[];
  created_at: string;
};

export type HeartRateLive = {
  bpm: number | null;
  measured_at: string | null;
  source: string;
  zone: "low" | "normal" | "elevated" | "high" | "unknown";
  zone_label: string;
  resting_baseline: number | null;
  latest_anomaly: HeartRateAnomaly | null;
};

export type HeartRateSummary = {
  average_bpm: number | null;
  min_bpm: number | null;
  max_bpm: number | null;
  resting_bpm: number | null;
  reading_count: number;
  window_hours: number;
};

export type ScenarioInfo = {
  scenario: string;
  available: Record<string, string>;
  source?: string;
};

export type EmergencyContact = {
  id: number;
  user_id: string;
  name: string;
  relationship: string;
  telegram_username: string | null;
  telegram_chat_id: string | null;
  pairing_code: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type Device = {
  id: number;
  user_id: string;
  name: string;
  device_id: string;
  status: string;
  last_seen_at: string | null;
  created_at: string;
  device_secret?: string;
};

export type NotificationAttempt = {
  contact_id: number;
  contact_name: string;
  ok: boolean;
  detail: string;
};

export type FallIncident = {
  id: number;
  user_id: string;
  device_id: number | null;
  event_timestamp: string;
  confidence: number | null;
  sensor_payload: Record<string, unknown>;
  status: string;
  telegram_notification_status: string;
  notification_detail: NotificationAttempt[];
  hr_context: Record<string, unknown> | null;
  created_at: string;
};
