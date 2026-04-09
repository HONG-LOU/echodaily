import { createAssessment, fetchLesson } from "../../utils/api";
import type { AssessmentMode, Lesson } from "../../types/api";

interface PracticePageData {
  loading: boolean;
  errorMessage: string;
  lesson: Lesson | null;
  mode: AssessmentMode;
  showReferenceText: boolean;
  recording: boolean;
  recordedDuration: number;
  tempFilePath: string;
  transcriptInput: string;
  submitting: boolean;
}

type PracticePageCustom = {
  lessonId: string;
  recorderManager: WechatMiniprogram.RecorderManager | null;
  audioContext: WechatMiniprogram.InnerAudioContext | null;
  loadLesson: (lessonId: string) => Promise<void>;
  setupRecorder: () => void;
  toggleMode: (event: WechatMiniprogram.BaseEvent) => void;
  revealReference: () => void;
  previewHint: () => void;
  startRecording: () => void;
  stopRecording: () => void;
  playRecording: () => void;
  onTranscriptInput: (event: WechatMiniprogram.CustomEvent<{ value: string }>) => void;
  submitAssessment: () => Promise<void>;
  handleRetry: () => void;
};

Page<PracticePageData, PracticePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    lesson: null,
    mode: "follow",
    showReferenceText: true,
    recording: false,
    recordedDuration: 0,
    tempFilePath: "",
    transcriptInput: "",
    submitting: false,
  },

  recorderManager: null,
  audioContext: null,
  lessonId: "",

  onLoad(query) {
    const mode = (query.mode || "follow") as AssessmentMode;
    const lessonId = query.lessonId || "";
    this.lessonId = lessonId;

    this.setData({
      mode,
      showReferenceText: mode === "follow",
    });
    this.setupRecorder();
    if (lessonId) {
      void this.loadLesson(lessonId);
    } else {
      this.setData({
        loading: false,
        errorMessage: "缺少 lessonId，请从首页重新进入。",
      });
    }
  },

  onUnload() {
    this.audioContext?.stop();
    this.audioContext?.destroy();
  },

  async loadLesson(lessonId) {
    this.setData({
      loading: true,
      errorMessage: "",
    });

    try {
      const lesson = await fetchLesson(lessonId);
      this.setData({
        lesson,
        loading: false,
      });
      wx.setNavigationBarTitle({
        title: lesson.title,
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "练习页加载失败。";
      this.setData({
        loading: false,
        errorMessage: message,
      });
    }
  },

  setupRecorder() {
    this.recorderManager = wx.getRecorderManager();
    this.audioContext = wx.createInnerAudioContext();

    this.recorderManager.onStart(() => {
      this.setData({
        recording: true,
      });
    });

    this.recorderManager.onStop((result) => {
      this.setData({
        recording: false,
        tempFilePath: result.tempFilePath,
        recordedDuration: Math.max(5, Math.round(result.duration / 1000)),
      });
    });

    this.recorderManager.onError(() => {
      this.setData({
        recording: false,
      });
      wx.showToast({
        title: "录音失败，请检查麦克风权限",
        icon: "none",
      });
    });
  },

  toggleMode(event) {
    const nextMode = String(event.currentTarget.dataset.mode || "follow") as AssessmentMode;
    this.setData({
      mode: nextMode,
      showReferenceText: nextMode === "follow",
    });
  },

  revealReference() {
    this.setData({
      showReferenceText: true,
    });
  },

  previewHint() {
    const lesson = this.data.lesson;
    if (!lesson) {
      return;
    }

    const content = this.data.mode === "follow" ? lesson.mode_hint : lesson.blind_box_prompt;
    wx.showModal({
      title: this.data.mode === "follow" ? "跟读提示" : "盲盒提示",
      content,
      showCancel: false,
      confirmText: "知道了",
    });
  },

  startRecording() {
    wx.authorize({
      scope: "scope.record",
      success: () => {
        this.recorderManager?.start({
          duration: 60000,
          sampleRate: 44100,
          numberOfChannels: 1,
          encodeBitRate: 192000,
          format: "mp3",
        });
      },
      fail: () => {
        wx.showModal({
          title: "需要录音权限",
          content: "请在微信开发者工具或真机里允许麦克风权限后继续。",
          showCancel: false,
          confirmText: "知道了",
        });
      },
    });
  },

  stopRecording() {
    this.recorderManager?.stop();
  },

  playRecording() {
    if (!this.data.tempFilePath) {
      wx.showToast({
        title: "先录一段再回放",
        icon: "none",
      });
      return;
    }

    if (!this.audioContext) {
      this.audioContext = wx.createInnerAudioContext();
    }
    this.audioContext.src = this.data.tempFilePath;
    this.audioContext.play();
  },

  onTranscriptInput(event) {
    this.setData({
      transcriptInput: event.detail.value,
    });
  },

  async submitAssessment() {
    const { lesson, mode, recordedDuration, transcriptInput } = this.data;
    if (!lesson) {
      return;
    }

    const trimmedTranscript = transcriptInput.trim();
    if (!recordedDuration && !trimmedTranscript) {
      wx.showToast({
        title: "请先录音，或补充练习文本",
        icon: "none",
      });
      return;
    }

    this.setData({
      submitting: true,
    });

    try {
      const report = await createAssessment({
        lesson_id: lesson.id,
        mode,
        duration_seconds: recordedDuration || lesson.estimated_seconds,
        transcript: trimmedTranscript || undefined,
      });
      const app = getApp<IAppOption>();
      app.globalData.lastAssessmentId = report.id;

      wx.navigateTo({
        url: `/pages/report/index?assessmentId=${report.id}`,
      });
    } catch (error) {
      wx.showToast({
        title: error instanceof Error ? error.message : "生成报告失败",
        icon: "none",
      });
    } finally {
      this.setData({
        submitting: false,
      });
    }
  },

  handleRetry() {
    if (this.lessonId) {
      void this.loadLesson(this.lessonId);
    }
  },
});
