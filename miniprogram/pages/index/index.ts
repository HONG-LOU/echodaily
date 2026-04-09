import { fetchDashboard } from "../../utils/api";
import type { DashboardResponse } from "../../types/api";

interface HomePageData {
  loading: boolean;
  errorMessage: string;
  dashboard: DashboardResponse | null;
}

type HomePageCustom = {
  loadDashboard: () => Promise<void>;
  startPractice: (event: WechatMiniprogram.BaseEvent) => void;
  openRecentReport: (event: WechatMiniprogram.BaseEvent) => void;
  handleRetry: () => void;
};

Page<HomePageData, HomePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    dashboard: null,
  },

  onLoad() {
    void this.loadDashboard();
  },

  onShow() {
    if (this.data.dashboard) {
      void this.loadDashboard();
    }
  },

  async onPullDownRefresh() {
    await this.loadDashboard();
    wx.stopPullDownRefresh();
  },

  async loadDashboard() {
    this.setData({
      loading: true,
      errorMessage: "",
    });

    try {
      const dashboard = await fetchDashboard();
      this.setData({
        dashboard,
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "首页加载失败，请稍后重试。";
      this.setData({
        errorMessage: message,
        loading: false,
      });
    }
  },

  startPractice(event) {
    const lessonId = String(event.currentTarget.dataset.lessonId || "");
    if (!lessonId) {
      wx.showToast({
        title: "今日任务暂不可用",
        icon: "none",
      });
      return;
    }

    wx.navigateTo({
      url: `/pages/practice/index?lessonId=${lessonId}`,
    });
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
    void this.loadDashboard();
  },

  onShareAppMessage() {
    const lessonTitle = this.data.dashboard?.today_lesson.title || "今日练习";
    return {
      title: `来和我一起读今天这句：${lessonTitle}`,
      path: "/pages/index/index",
    };
  },
});
