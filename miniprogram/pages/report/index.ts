import { fetchAssessment } from "../../utils/api";
import type { AssessmentDetail, AssessmentHighlight } from "../../types/api";

interface ReportPageData {
  loading: boolean;
  errorMessage: string;
  report: AssessmentDetail | null;
  primaryHighlights: AssessmentHighlight[];
}

type ReportPageCustom = {
  assessmentId: string;
  loadReport: (assessmentId: string) => Promise<void>;
  goPracticeAgain: () => void;
  goHome: () => void;
  handleRetry: () => void;
};

Page<ReportPageData, ReportPageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    report: null,
    primaryHighlights: [],
  },

  assessmentId: "",

  onLoad(query) {
    this.assessmentId = query.assessmentId || getApp<IAppOption>().globalData.lastAssessmentId || "";
    if (!this.assessmentId) {
      this.setData({
        loading: false,
        errorMessage: "缺少 assessmentId，请先完成一次练习。",
      });
      return;
    }
    void this.loadReport(this.assessmentId);
  },

  async loadReport(assessmentId) {
    this.setData({
      loading: true,
      errorMessage: "",
    });

    try {
      const report = await fetchAssessment(assessmentId);
      this.setData({
        report,
        primaryHighlights: report.highlights,
        loading: false,
      });
      wx.setNavigationBarTitle({
        title: `${report.overall_score} 分报告`,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "报告加载失败。";
      this.setData({
        loading: false,
        errorMessage: message,
        primaryHighlights: [],
      });
    }
  },

  goPracticeAgain() {
    const report = this.data.report;
    if (!report) {
      return;
    }
    wx.navigateTo({
      url: `/pages/practice/index?lessonId=${report.lesson_id}`,
    });
  },

  goHome() {
    wx.switchTab({
      url: "/pages/index/index",
    });
  },

  handleRetry() {
    if (this.assessmentId) {
      void this.loadReport(this.assessmentId);
    }
  },
});
