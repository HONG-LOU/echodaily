import { fetchProfile } from "../../utils/api";
import type { MistakeNotebookEntry, ProfileResponse, RecentPractice } from "../../types/api";

interface ProfilePageData {
  loading: boolean;
  errorMessage: string;
  profile: ProfileResponse | null;
  topMistake: MistakeNotebookEntry | null;
  latestPractice: RecentPractice | null;
  secondPractice: RecentPractice | null;
}

type ProfilePageCustom = {
  loadProfile: () => Promise<void>;
  openRecentReport: (event: WechatMiniprogram.BaseEvent) => void;
  handleRetry: () => void;
};

Page<ProfilePageData, ProfilePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    profile: null,
    topMistake: null,
    latestPractice: null,
    secondPractice: null,
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
      this.setData({
        profile,
        topMistake: profile.mistake_notebook[0] || null,
        latestPractice: profile.recent_practices[0] || null,
        secondPractice: profile.recent_practices[1] || null,
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "个人中心加载失败。";
      this.setData({
        errorMessage: message,
        topMistake: null,
        latestPractice: null,
        secondPractice: null,
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
});
