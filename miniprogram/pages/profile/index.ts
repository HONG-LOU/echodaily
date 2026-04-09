import { fetchProfile, getApiBaseUrl, saveApiBaseUrl } from "../../utils/api";
import type { ProfileResponse } from "../../types/api";

interface ProfilePageData {
  loading: boolean;
  errorMessage: string;
  profile: ProfileResponse | null;
  apiBaseUrl: string;
  apiInputValue: string;
}

type ProfilePageCustom = {
  loadProfile: () => Promise<void>;
  onApiInput: (event: WechatMiniprogram.CustomEvent<{ value: string }>) => void;
  saveBackendAddress: () => void;
  openRecentReport: (event: WechatMiniprogram.BaseEvent) => void;
  previewCoach: () => void;
  handleRetry: () => void;
};

Page<ProfilePageData, ProfilePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    profile: null,
    apiBaseUrl: "",
    apiInputValue: "",
  },

  onLoad() {
    const apiBaseUrl = getApiBaseUrl();
    this.setData({
      apiBaseUrl,
      apiInputValue: apiBaseUrl,
    });
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

  onApiInput(event) {
    this.setData({
      apiInputValue: event.detail.value,
    });
  },

  saveBackendAddress() {
    const nextValue = this.data.apiInputValue.trim();
    if (!nextValue) {
      wx.showToast({
        title: "请输入后端地址",
        icon: "none",
      });
      return;
    }

    const normalized = saveApiBaseUrl(nextValue);
    this.setData({
      apiBaseUrl: normalized,
      apiInputValue: normalized,
    });
    wx.showToast({
      title: "地址已保存",
      icon: "success",
    });
    void this.loadProfile();
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

  previewCoach() {
    const wechatHint = this.data.profile?.coach_cta.wechat_hint || "EchoCoach_2026";
    wx.showModal({
      title: "私域入口预留",
      content: `当前示例老师微信为 ${wechatHint}。后续你可以替换成企微活码或客服组件。`,
      showCancel: false,
      confirmText: "继续完善",
    });
  },

  handleRetry() {
    void this.loadProfile();
  },
});
