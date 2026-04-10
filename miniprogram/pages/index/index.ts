import { fetchDashboard, fetchRecentLessons } from "../../utils/api";
import type { DashboardResponse, RecentScore, Lesson } from "../../types/api";

interface HomePageData {
  loading: boolean;
  errorMessage: string;
  dashboard: DashboardResponse | null;
  latestScore: RecentScore | null;
  playingOriginal: boolean;
  recentLessons: Lesson[];
  currentLessonIndex: number;
  swipeIndicators: number[];
}

type HomePageCustom = {
  ttsAudioContext: WechatMiniprogram.InnerAudioContext | null;
  loadDashboard: () => Promise<void>;
  playOriginalAudio: () => void;
  startPractice: (event: WechatMiniprogram.BaseEvent) => void;
  onSwiperChange: (event: WechatMiniprogram.SwiperChange) => void;
  updateSwipeIndicators: (currentIndex: number, total: number) => void;
  openRecentReport: (event: WechatMiniprogram.BaseEvent) => void;
  handleRetry: () => void;
};

Page<HomePageData, HomePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    dashboard: null,
    latestScore: null,
    playingOriginal: false,
    recentLessons: [],
    currentLessonIndex: 0,
    swipeIndicators: [],
  },

  ttsAudioContext: null,

  onLoad() {
    void this.loadDashboard();
  },

  onShow() {
    if (this.data.dashboard) {
      void this.loadDashboard();
    }
  },

  onHide() {
    this.ttsAudioContext?.stop();
    this.setData({ playingOriginal: false });
  },

  onUnload() {
    this.ttsAudioContext?.stop();
    this.ttsAudioContext?.destroy();
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
      const [dashboard, recentLessons] = await Promise.all([
        fetchDashboard(),
        fetchRecentLessons().catch(() => []),
      ]);
      
      const safeRecentLessons = recentLessons && recentLessons.length > 0 
        ? recentLessons 
        : [dashboard.today_lesson];

      this.setData({
        dashboard,
        recentLessons: safeRecentLessons,
        currentLessonIndex: 0,
        swipeIndicators: [],
        latestScore: dashboard.recent_scores[0] || null,
        loading: false,
      });
      this.updateSwipeIndicators(0, safeRecentLessons.length);
    } catch (error) {
      const message = error instanceof Error ? error.message : "首页加载失败，请稍后重试。";
      this.setData({
        errorMessage: message,
        latestScore: null,
        loading: false,
      });
    }
  },

  playOriginalAudio() {
    const lesson = this.data.recentLessons[this.data.currentLessonIndex] || this.data.dashboard?.today_lesson;
    if (!lesson || !lesson.audio_url) {
      wx.showToast({
        title: "暂无原声",
        icon: "none",
      });
      return;
    }

    if (this.data.playingOriginal) {
      this.ttsAudioContext?.stop();
      this.setData({ playingOriginal: false });
      return;
    }

    if (!this.ttsAudioContext) {
      this.ttsAudioContext = wx.createInnerAudioContext();
      this.ttsAudioContext.onEnded(() => {
        this.setData({ playingOriginal: false });
      });
      this.ttsAudioContext.onError(() => {
        this.setData({ playingOriginal: false });
        wx.showToast({
          title: "原声播放失败",
          icon: "none",
        });
      });
    }

    this.ttsAudioContext.src = lesson.audio_url;
    this.ttsAudioContext.play();
    this.setData({ playingOriginal: true });
  },

  onSwiperChange(event) {
    const nextIndex = event.detail.current;
    this.setData({
      currentLessonIndex: nextIndex,
    });
    this.updateSwipeIndicators(nextIndex, this.data.recentLessons.length);
    if (this.data.playingOriginal) {
      this.ttsAudioContext?.stop();
      this.setData({ playingOriginal: false });
    }
  },

  updateSwipeIndicators(currentIndex, total) {
    const maxDots = 6;
    if (total <= 0) {
      this.setData({ swipeIndicators: [] });
      return;
    }

    if (total <= maxDots) {
      this.setData({
        swipeIndicators: Array.from({ length: total }, (_, index) => index),
      });
      return;
    }

    const half = Math.floor(maxDots / 2);
    let start = Math.max(0, currentIndex - half);
    if (start + maxDots > total) {
      start = total - maxDots;
    }
    this.setData({
      swipeIndicators: Array.from({ length: maxDots }, (_, index) => start + index),
    });
  },

  startPractice(event) {
    const lessonId = String(event.currentTarget.dataset.lessonId || "");
    if (!lessonId) {
      wx.showToast({
        title: "今天的练习暂时不可用",
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
    const lessonTitle = this.data.recentLessons[this.data.currentLessonIndex]?.title || this.data.dashboard?.today_lesson.title || "今日练习";
    return {
      title: `来和我一起读今天这句：${lessonTitle}`,
      path: "/pages/index/index",
    };
  },
});
