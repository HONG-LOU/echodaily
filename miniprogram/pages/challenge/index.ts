import { fetchChallenges } from "../../utils/api";
import type { ChallengeSummary } from "../../types/api";

interface ChallengePageData {
  loading: boolean;
  errorMessage: string;
  challenges: ChallengeSummary[];
}

type ChallengePageCustom = {
  loadChallenges: () => Promise<void>;
  joinChallenge: (event: WechatMiniprogram.BaseEvent) => void;
  handleRetry: () => void;
};

Page<ChallengePageData, ChallengePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    challenges: [],
  },

  onLoad() {
    void this.loadChallenges();
  },

  onShow() {
    if (this.data.challenges.length) {
      void this.loadChallenges();
    }
  },

  async loadChallenges() {
    this.setData({
      loading: true,
      errorMessage: "",
    });

    try {
      const challenges = await fetchChallenges();
      this.setData({
        challenges,
        loading: false,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "挑战信息加载失败。";
      this.setData({
        errorMessage: message,
        loading: false,
      });
    }
  },

  joinChallenge(event) {
    const title = String(event.currentTarget.dataset.title || "挑战营");
    wx.showModal({
      title: "MVP 提示",
      content: `当前先完成展示和转化链路，${title} 的支付与报名可在下一步接微信支付与订单系统。`,
      showCancel: false,
      confirmText: "知道了",
    });
  },

  handleRetry() {
    void this.loadChallenges();
  },

  onShareAppMessage() {
    return {
      title: "和我一起参加 21 天朗读挑战营",
      path: "/pages/challenge/index",
    };
  },
});
