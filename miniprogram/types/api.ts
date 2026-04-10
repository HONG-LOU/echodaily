export interface DashboardUser {
  id: string;
  nickname: string;
  avatar_symbol: string;
  avatar_url: string | null;
  streak_days: number;
  total_practices: number;
  weekly_minutes: number;
  weak_sound: string;
  city: string;
  bio: string;
}

export interface StatCard {
  label: string;
  value: string;
  caption: string;
}

export interface Lesson {
  id: string;
  title: string;
  subtitle: string;
  pack_name: string;
  english_text: string;
  translation: string;
  scenario: string;
  mode_hint: string;
  tags: string[];
  difficulty: string;
  estimated_seconds: number;
  theme_tone: string;
}

export interface RecentScore {
  assessment_id: string;
  lesson_title: string;
  overall_score: number;
  practiced_at: string;
}

export interface DashboardResponse {
  daily_message: string;
  user: DashboardUser;
  today_lesson: Lesson;
  quick_stats: StatCard[];
  recent_scores: RecentScore[];
}

export interface AssessmentDimension {
  key: string;
  label: string;
  score: number;
}

export interface AssessmentHighlight {
  word: string;
  expected_ipa: string;
  observed_ipa: string;
  accuracy_score: number;
  observed_issue: string;
  coach_tip: string;
  severity: "low" | "medium" | "high";
}

export interface AssessmentDetail {
  id: string;
  lesson_id: string;
  lesson_title: string;
  lesson_text: string;
  translation: string;
  duration_seconds: number;
  recognized_text: string;
  overall_score: number;
  mistake_count: number;
  headline: string;
  encouragement: string;
  created_at: string;
  dimensions: AssessmentDimension[];
  highlights: AssessmentHighlight[];
}

export interface AssessmentCreatePayload {
  lesson_id: string;
  duration_seconds: number;
  audio_format: "mp3" | "wav" | "pcm" | "speex";
  audio_base64: string;
}

export interface MistakeNotebookEntry {
  word: string;
  expected_ipa: string;
  coach_tip: string;
  lesson_title: string;
  score: number;
}

export interface RecentPractice {
  assessment_id: string;
  lesson_title: string;
  score: number;
  practiced_at: string;
}

export interface ProfileResponse {
  id: string;
  nickname: string;
  avatar_symbol: string;
  avatar_url: string | null;
  city: string;
  bio: string;
  streak_days: number;
  total_practices: number;
  weekly_minutes: number;
  weak_sound: string;
  mistake_notebook: MistakeNotebookEntry[];
  recent_practices: RecentPractice[];
}

export interface AuthenticatedUser {
  id: string;
  nickname: string;
  avatar_symbol: string;
  avatar_url: string | null;
  city: string;
  bio: string;
}

export interface WechatLoginResponse {
  access_token: string;
  token_type: "Bearer";
  expires_at: string;
  is_new_user: boolean;
  user: AuthenticatedUser;
}
