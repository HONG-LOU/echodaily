import { fetchProfile } from "../../utils/api";
import type { MistakeNotebookEntry, ProfileResponse, RecentPractice } from "../../types/api";

interface ProfilePageData {
  loading: boolean;
  errorMessage: string;
  profile: ProfileResponse | null;
  topMistake: MistakeNotebookEntry | null;
  latestPractice: RecentPractice | null;
  secondPractice: RecentPractice | null;
  calendarDays: { date: string; active: boolean }[];
  showPoster: boolean;
}

type ProfilePageCustom = {
  loadProfile: () => Promise<void>;
  openRecentReport: (event: WechatMiniprogram.BaseEvent) => void;
  handleRetry: () => void;
  openPoster: () => void;
  closePoster: () => void;
};

Page<ProfilePageData, ProfilePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    profile: null,
    topMistake: null,
    latestPractice: null,
    secondPractice: null,
    calendarDays: [],
    showPoster: false,
  },

  onLoad() {
    void this.loadProfile();
  },

  onShow() {
    if (this.data.profile) {
      void this.loadProfile();
    }
  },

  async loadProfile() {
    this.setData({
      loading: true,
      errorMessage: "",
    });

    try {
      const profile = await fetchProfile();
      
      // Generate calendar days (last 30 days)
      const calendarDays = [];
      const today = new Date();
      for (let i = 29; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(today.getDate() - i);
        const dateStr = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
        calendarDays.push({
          date: dateStr,
          active: profile.check_in_dates.includes(dateStr)
        });
      }

      this.setData({
        profile,
        topMistake: profile.mistake_notebook[0] || null,
        latestPractice: profile.recent_practices[0] || null,
        secondPractice: profile.recent_practices[1] || null,
        calendarDays,
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "个人中心加载失败。";
      this.setData({
        errorMessage: message,
        topMistake: null,
        latestPractice: null,
        secondPractice: null,
        calendarDays: [],
        loading: false,
      });
    }
  },

  openRecentReport(event) {
    const assessmentId = String(event.currentTarget.dataset.assessmentId || "");
    if (!assessmentId) {
      return;
    }
    wx.navigateTo({
      url: `/pages/report/index?assessmentId=${assessmentId}`,
    });
  },

  handleRetry() {
    void this.loadProfile();
  },

  openPoster() {
    this.setData({ showPoster: true });
  },

  closePoster() {
    this.setData({ showPoster: false });
  }
});
