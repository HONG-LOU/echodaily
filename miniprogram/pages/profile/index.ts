import { fetchProfile } from "../../utils/api";
import type { ProfileResponse } from "../../types/api";

interface ProfilePageData {
  loading: boolean;
  errorMessage: string;
  profile: ProfileResponse | null;
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
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "个人中心加载失败。";
      this.setData({
        errorMessage: message,
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
