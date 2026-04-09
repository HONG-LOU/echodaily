export type AssessmentMode = "follow" | "blind_box";

export interface DashboardUser {
  id: string;
  nickname: string;
  avatar_symbol: string;
  streak_days: number;
  total_practices: number;
  weekly_minutes: number;
  plan_name: string;
  weak_sound: string;
  target_pack: string;
  focus_tag: string;
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
  blind_box_prompt: string;
  tags: string[];
  difficulty: string;
  estimated_seconds: number;
  poster_blurb: string;
  theme_tone: string;
}

export interface RecentScore {
  assessment_id: string;
  lesson_title: string;
  overall_score: number;
  practiced_at: string;
}

export interface MembershipOffer {
  title: string;
  monthly_price: string;
  yearly_price: string;
  highlights: string[];
  call_to_action: string;
}

export interface PartnerPitch {
  title: string;
  summary: string;
  bullets: string[];
  call_to_action: string;
}

export interface ChallengeSummary {
  id: string;
  title: string;
  description: string;
  deposit_amount: number;
  participants: number;
  days_total: number;
  days_left: number;
  score_threshold: number;
  reward_pool: number;
  teaser: string;
}

export interface DashboardResponse {
  user: DashboardUser;
  today_lesson: Lesson;
  quick_stats: StatCard[];
  challenge_spotlight: {
    title: string;
    participants: number;
    days_left: number;
    deposit_amount: number;
    reward_pool: number;
    score_threshold: number;
    teaser: string;
  };
  membership_offer: MembershipOffer;
  partner_pitch: PartnerPitch;
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
  mode: AssessmentMode;
  duration_seconds: number;
  transcript: string | null;
  transcript_used: boolean;
  overall_score: number;
  comparison_ratio: number;
  mistake_count: number;
  headline: string;
  encouragement: string;
  poster_caption: string;
  poster_theme: string;
  created_at: string;
  dimensions: AssessmentDimension[];
  highlights: AssessmentHighlight[];
}

export interface AssessmentCreatePayload {
  user_id: string;
  lesson_id: string;
  mode: AssessmentMode;
  duration_seconds: number;
  transcript?: string;
}

export interface Badge {
  name: string;
  description: string;
  unlocked: boolean;
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
  poster_caption: string;
  practiced_at: string;
}

export interface ProfileResponse {
  nickname: string;
  avatar_symbol: string;
  city: string;
  bio: string;
  streak_days: number;
  total_practices: number;
  weekly_minutes: number;
  weak_sound: string;
  target_pack: string;
  plan_name: string;
  pro_active: boolean;
  badges: Badge[];
  mistake_notebook: MistakeNotebookEntry[];
  recent_practices: RecentPractice[];
  coach_cta: {
    title: string;
    description: string;
    wechat_hint: string;
  };
  membership_hint: {
    title: string;
    description: string;
    highlights: string[];
  };
}
