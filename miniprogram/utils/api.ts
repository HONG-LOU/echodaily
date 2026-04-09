import type {
  AssessmentCreatePayload,
  AssessmentDetail,
  ChallengeSummary,
  DashboardResponse,
  Lesson,
  ProfileResponse,
} from "../types/api";

type RequestOverrides = Omit<
  WechatMiniprogram.RequestOption<WechatMiniprogram.IAnyObject>,
  "url" | "success" | "fail"
>;

function normalizeApiBaseUrl(value: unknown, fallback: string): string {
  const normalized = String(value || "")
    .trim()
    .replace(/\/$/, "");

  if (!normalized || !/^https?:\/\//.test(normalized)) {
    return fallback;
  }

  return normalized;
}

function getRuntimeConfig(): { apiBaseUrl: string; userId: string } {
  const app = getApp<IAppOption>();
  const storedApiBaseUrl = wx.getStorageSync("apiBaseUrl");
  const storedUserId = wx.getStorageSync("userId");
  const resolvedApiBaseUrl = normalizeApiBaseUrl(storedApiBaseUrl, app.globalData.apiBaseUrl);

  return {
    apiBaseUrl: resolvedApiBaseUrl,
    userId: storedUserId || app.globalData.userId,
  };
}

export function getApiBaseUrl(): string {
  return getRuntimeConfig().apiBaseUrl;
}

export function getDefaultUserId(): string {
  return getRuntimeConfig().userId;
}

export function saveApiBaseUrl(nextBaseUrl: string): string {
  const normalizedBaseUrl = nextBaseUrl.trim().replace(/\/$/, "");
  const app = getApp<IAppOption>();
  app.globalData.apiBaseUrl = normalizedBaseUrl;
  wx.setStorageSync("apiBaseUrl", normalizedBaseUrl);
  return normalizedBaseUrl;
}

function request<T>(path: string, options?: RequestOverrides): Promise<T> {
  const { apiBaseUrl } = getRuntimeConfig();
  const url = `${apiBaseUrl}${path}`;
  const method = String(options?.method || "GET").toUpperCase();

  const executeRequest = () =>
    new Promise<T>((resolve, reject) => {
      wx.request({
        ...options,
        url,
        timeout: 20000,
        success: (response) => {
          const { statusCode, data } = response;
          if (typeof statusCode === "number" && statusCode >= 200 && statusCode < 300) {
            resolve(data as T);
            return;
          }

          const fallbackMessage =
            typeof data === "object" && data && "message" in data
              ? String((data as { message?: string }).message)
              : "请求失败，请检查后端服务是否可用。";
          reject(new Error(fallbackMessage));
        },
        fail: (error) => {
          const errMsg =
            typeof error === "object" && error && "errMsg" in error ? String(error.errMsg) : "";
          console.warn("[api] request failed", {
            method,
            url,
            errMsg,
          });

          if (errMsg.includes("timeout")) {
            reject(new Error("请求超时，请稍后重试，或确认正式域名配置已生效。"));
            return;
          }

          reject(new Error("网络连接失败，请确认正式域名已配置到小程序后台并已生效。"));
        },
      });
    });

  return executeRequest().catch((error) => {
    if (method !== "GET" || !(error instanceof Error) || !error.message.includes("请求超时")) {
      throw error;
    }

    console.warn("[api] retry once after timeout", {
      method,
      url,
    });
    return executeRequest();
  });
}

export function fetchDashboard(): Promise<DashboardResponse> {
  const { userId } = getRuntimeConfig();
  return request<DashboardResponse>(`/dashboard?user_id=${encodeURIComponent(userId)}`);
}

export function fetchLesson(lessonId: string): Promise<Lesson> {
  return request<Lesson>(`/lessons/${lessonId}`);
}

export function fetchTodayLesson(): Promise<Lesson> {
  return request<Lesson>("/lessons/today");
}

export function createAssessment(payload: AssessmentCreatePayload): Promise<AssessmentDetail> {
  return request<AssessmentDetail>("/assessments", {
    method: "POST",
    data: payload,
    header: {
      "content-type": "application/json",
    },
  });
}

export function fetchAssessment(assessmentId: string): Promise<AssessmentDetail> {
  return request<AssessmentDetail>(`/assessments/${assessmentId}`);
}

export function fetchChallenges(): Promise<ChallengeSummary[]> {
  return request<ChallengeSummary[]>("/challenges");
}

export function fetchProfile(): Promise<ProfileResponse> {
  const { userId } = getRuntimeConfig();
  return request<ProfileResponse>(`/profile?user_id=${encodeURIComponent(userId)}`);
}
