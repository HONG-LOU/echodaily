import { createAssessment, fetchLesson } from "../../utils/api";
import type { Lesson } from "../../types/api";

interface PracticePageData {
  loading: boolean;
  errorMessage: string;
  lesson: Lesson | null;
  recording: boolean;
  recordedDuration: number;
  tempFilePath: string;
  submitting: boolean;
  playingOriginal: boolean;
}

type PracticePageCustom = {
  lessonId: string;
  recorderManager: WechatMiniprogram.RecorderManager | null;
  audioContext: WechatMiniprogram.InnerAudioContext | null;
  ttsAudioContext: WechatMiniprogram.InnerAudioContext | null;
  loadLesson: (lessonId: string) => Promise<void>;
  setupRecorder: () => void;
  previewHint: () => void;
  playOriginalAudio: () => void;
  startRecording: () => void;
  stopRecording: () => void;
  playRecording: () => void;
  readRecordedAudio: () => Promise<string>;
  submitAssessment: () => Promise<void>;
  handleRetry: () => void;
};

Page<PracticePageData, PracticePageCustom>({
  data: {
    loading: true,
    errorMessage: "",
    lesson: null,
    recording: false,
    recordedDuration: 0,
    tempFilePath: "",
    submitting: false,
    playingOriginal: false,
  },

  recorderManager: null,
  audioContext: null,
  ttsAudioContext: null,
  lessonId: "",

  onLoad(query) {
    const lessonId = query.lessonId || "";
    this.lessonId = lessonId;

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
    this.ttsAudioContext?.stop();
    this.ttsAudioContext?.destroy();
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
        tempFilePath: "",
        recordedDuration: 0,
      });
    });

    this.recorderManager.onStop((result) => {
      this.setData({
        recording: false,
        tempFilePath: result.tempFilePath,
        recordedDuration: Math.max(1, Math.round(result.duration / 1000)),
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

  previewHint() {
    const lesson = this.data.lesson;
    if (!lesson) {
      return;
    }

    wx.showModal({
      title: "跟读提示",
      content: lesson.mode_hint,
      showCancel: false,
      confirmText: "知道了",
    });
  },

  playOriginalAudio() {
    const lesson = this.data.lesson;
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

  startRecording() {
    wx.authorize({
      scope: "scope.record",
      success: () => {
        this.recorderManager?.start({
          duration: 60000,
          sampleRate: 16000,
          numberOfChannels: 1,
          encodeBitRate: 96000,
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

  readRecordedAudio() {
    const { tempFilePath } = this.data;
    if (!tempFilePath) {
      return Promise.reject(new Error("请先完成录音。"));
    }

    return new Promise((resolve, reject) => {
      wx.getFileSystemManager().readFile({
        filePath: tempFilePath,
        encoding: "base64",
        success: (result) => {
          if (typeof result.data === "string" && result.data.trim()) {
            resolve(result.data);
            return;
          }

          reject(new Error("录音文件读取失败。"));
        },
        fail: () => {
          reject(new Error("录音文件读取失败。"));
        },
      });
    });
  },

  async submitAssessment() {
    const { lesson, recordedDuration } = this.data;
    if (!lesson) {
      return;
    }
    if (!this.data.tempFilePath) {
      wx.showToast({
        title: "请先录音",
        icon: "none",
      });
      return;
    }

    this.setData({
      submitting: true,
    });

    try {
      const audioBase64 = await this.readRecordedAudio();
      const report = await createAssessment({
        lesson_id: lesson.id,
        duration_seconds: recordedDuration || lesson.estimated_seconds,
        audio_format: "mp3",
        audio_base64: audioBase64,
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
