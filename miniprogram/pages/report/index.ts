import { fetchAssessment } from "../../utils/api";
import type { AssessmentDetail } from "../../types/api";

interface ReportPageData {
  loading: boolean;
  errorMessage: string;
  report: AssessmentDetail | null;
}

type ReportPageCustom = {
  assessmentId: string;
  loadReport: (assessmentId: string) => Promise<void>;
  drawRadar: () => void;
  goPracticeAgain: () => void;
  goHome: () => void;
  handleRetry: () => void;
};

Page<ReportPageData, ReportPageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    report: null,
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
        loading: false,
      });
      wx.setNavigationBarTitle({
        title: `${report.overall_score} 分回音报告`,
      });
      wx.nextTick(() => {
        this.drawRadar();
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "报告加载失败。";
      this.setData({
        loading: false,
        errorMessage: message,
      });
    }
  },

  drawRadar() {
    const report = this.data.report;
    if (!report) {
      return;
    }

    const ctx = wx.createCanvasContext("radarCanvas", this);
    const size = 280;
    const center = size / 2;
    const radius = 92;
    const metrics = report.dimensions;

    ctx.clearRect(0, 0, size, size);

    for (let level = 1; level <= 4; level += 1) {
      const levelRadius = (radius / 4) * level;
      ctx.beginPath();
      metrics.forEach((_, index) => {
        const angle = (-90 + (360 / metrics.length) * index) * (Math.PI / 180);
        const x = center + Math.cos(angle) * levelRadius;
        const y = center + Math.sin(angle) * levelRadius;
        if (index === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.closePath();
      ctx.setStrokeStyle("rgba(109, 92, 73, 0.1)");
      ctx.stroke();
    }

    metrics.forEach((metric, index) => {
      const angle = (-90 + (360 / metrics.length) * index) * (Math.PI / 180);
      const axisX = center + Math.cos(angle) * radius;
      const axisY = center + Math.sin(angle) * radius;
      ctx.beginPath();
      ctx.moveTo(center, center);
      ctx.lineTo(axisX, axisY);
      ctx.setStrokeStyle("rgba(109, 92, 73, 0.1)");
      ctx.stroke();

      const labelX = center + Math.cos(angle) * (radius + 28);
      const labelY = center + Math.sin(angle) * (radius + 28);
      ctx.setFillStyle("#857565");
      ctx.setFontSize(12);
      ctx.fillText(metric.label, labelX - 14, labelY);
    });

    ctx.beginPath();
    metrics.forEach((metric, index) => {
      const angle = (-90 + (360 / metrics.length) * index) * (Math.PI / 180);
      const metricRadius = radius * (metric.score / 100);
      const x = center + Math.cos(angle) * metricRadius;
      const y = center + Math.sin(angle) * metricRadius;
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.closePath();
    ctx.setFillStyle("rgba(223, 171, 120, 0.24)");
    ctx.fill();
    ctx.setStrokeStyle("#d8a16f");
    ctx.stroke();

    metrics.forEach((metric, index) => {
      const angle = (-90 + (360 / metrics.length) * index) * (Math.PI / 180);
      const metricRadius = radius * (metric.score / 100);
      const x = center + Math.cos(angle) * metricRadius;
      const y = center + Math.sin(angle) * metricRadius;
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, Math.PI * 2);
      ctx.setFillStyle("#efc6a1");
      ctx.fill();
    });

    ctx.draw();
  },

  goPracticeAgain() {
    const report = this.data.report;
    if (!report) {
      return;
    }
    wx.navigateTo({
      url: `/pages/practice/index?lessonId=${report.lesson_id}&mode=${report.mode}`,
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

  onShareAppMessage() {
    const report = this.data.report;
    if (!report) {
      return {
        title: "来看看我的每日回音报告",
        path: "/pages/index/index",
      };
    }

    return {
      title: `我在 EchoDaily 拿到了 ${report.overall_score} 分`,
      path: "/pages/index/index",
    };
  },
});
