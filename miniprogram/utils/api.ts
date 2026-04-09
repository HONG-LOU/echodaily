import type {
  AssessmentCreatePayload,
  AssessmentDetail,
  DashboardResponse,
  Lesson,
  ProfileResponse,
  WechatLoginResponse,
} from "../types/api";

type RequestOverrides = Omit<
  WechatMiniprogram.RequestOption<WechatMiniprogram.IAnyObject>,
  "url" | "success" | "fail"
>;

class ApiError extends Error {
  statusCode?: number;

  constructor(message: string, statusCode?: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

function normalizeApiBaseUrl(value: unknown, fallback: string): string {
  const normalized = String(value || "")
    .trim()
    .replace(/\/$/, "");

  if (!normalized || !/^https?:\/\//.test(normalized)) {
    return fallback;
  }

  return normalized;
}

function getRuntimeConfig(): {
  apiBaseUrl: string;
  accessToken: string;
  tokenExpiresAt: string;
} {
  const app = getApp<IAppOption>();
  const storedApiBaseUrl = wx.getStorageSync("apiBaseUrl");
  const storedAccessToken = wx.getStorageSync("accessToken");
  const storedTokenExpiresAt = wx.getStorageSync("tokenExpiresAt");
  const resolvedApiBaseUrl = normalizeApiBaseUrl(storedApiBaseUrl, app.globalData.apiBaseUrl);

  return {
    apiBaseUrl: resolvedApiBaseUrl,
    accessToken: String(storedAccessToken || app.globalData.accessToken || ""),
    tokenExpiresAt: String(storedTokenExpiresAt || app.globalData.tokenExpiresAt || ""),
  };
}

function hasValidAccessToken(accessToken: string, tokenExpiresAt: string): boolean {
  if (!accessToken || !tokenExpiresAt) {
    return false;
  }

  const expiresAt = Date.parse(tokenExpiresAt);
  if (Number.isNaN(expiresAt)) {
    return false;
  }

  return expiresAt - Date.now() > 60 * 1000;
}

function saveAuthSession(payload: WechatLoginResponse): void {
  const app = getApp<IAppOption>();
  app.globalData.accessToken = payload.access_token;
  app.globalData.tokenExpiresAt = payload.expires_at;
  app.globalData.userId = payload.user.id;
  wx.setStorageSync("accessToken", payload.access_token);
  wx.setStorageSync("tokenExpiresAt", payload.expires_at);
  wx.setStorageSync("userId", payload.user.id);
}

function clearAuthSession(): void {
  const app = getApp<IAppOption>();
  app.globalData.accessToken = "";
  app.globalData.tokenExpiresAt = "";
  app.globalData.userId = "";
  wx.removeStorageSync("accessToken");
  wx.removeStorageSync("tokenExpiresAt");
  wx.removeStorageSync("userId");
}

function runWxLogin(): Promise<string> {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (result) => {
        if (result.code) {
          resolve(result.code);
          return;
        }

        reject(new Error("微信登录失败，未拿到有效 code。"));
      },
      fail: () => {
        reject(new Error("微信登录失败，请检查开发者工具或真机登录状态。"));
      },
    });
  });
}

function executeRequestOnce<T>(url: string, options?: RequestOverrides): Promise<T> {
  const method = String(options?.method || "GET").toUpperCase();

  return new Promise<T>((resolve, reject) => {
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
        reject(new ApiError(fallbackMessage, typeof statusCode === "number" ? statusCode : 0));
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
          reject(new ApiError("请求超时，请稍后重试，或确认正式域名配置已生效。"));
          return;
        }

        reject(new ApiError("网络连接失败，请确认正式域名已配置到小程序后台并已生效。"));
      },
    });
  });
}

function executeRequest<T>(url: string, options?: RequestOverrides): Promise<T> {
  const method = String(options?.method || "GET").toUpperCase();

  return executeRequestOnce<T>(url, options).catch((error) => {
    if (method !== "GET" || !(error instanceof Error) || !error.message.includes("请求超时")) {
      throw error;
    }

    console.warn("[api] retry once after timeout", {
      method,
      url,
    });
    return executeRequestOnce<T>(url, options);
  });
}

let loginPromise: Promise<void> | null = null;

async function loginWithWeChat(): Promise<void> {
  const { apiBaseUrl } = getRuntimeConfig();
  const code = await runWxLogin();
  const payload = await executeRequest<WechatLoginResponse>(`${apiBaseUrl}/auth/wechat/login`, {
    method: "POST",
    data: { code },
    header: {
      "content-type": "application/json",
    },
  });
  saveAuthSession(payload);
}

export function ensureAuthorized(forceRefresh = false): Promise<void> {
  const { accessToken, tokenExpiresAt } = getRuntimeConfig();
  if (!forceRefresh && hasValidAccessToken(accessToken, tokenExpiresAt)) {
    return Promise.resolve();
  }

  if (loginPromise) {
    return loginPromise;
  }

  loginPromise = loginWithWeChat().finally(() => {
    loginPromise = null;
  });
  return loginPromise;
}

async function request<T>(path: string, options?: RequestOverrides): Promise<T> {
  await ensureAuthorized();
  const { apiBaseUrl, accessToken } = getRuntimeConfig();
  const requestOptions: RequestOverrides = {
    ...options,
    header: {
      ...(options?.header || {}),
      Authorization: `Bearer ${accessToken}`,
    },
  };

  try {
    return await executeRequest<T>(`${apiBaseUrl}${path}`, requestOptions);
  } catch (error) {
    if (!(error instanceof ApiError) || error.statusCode !== 401) {
      throw error;
    }

    clearAuthSession();
    await ensureAuthorized(true);
    const {
      apiBaseUrl: refreshedApiBaseUrl,
      accessToken: refreshedAccessToken,
    } = getRuntimeConfig();
    return executeRequest<T>(`${refreshedApiBaseUrl}${path}`, {
      ...options,
      header: {
        ...(options?.header || {}),
        Authorization: `Bearer ${refreshedAccessToken}`,
      },
    });
  }
}

export function fetchDashboard(): Promise<DashboardResponse> {
  return request<DashboardResponse>("/dashboard");
}

export function fetchLesson(lessonId: string): Promise<Lesson> {
  return request<Lesson>(`/lessons/${lessonId}`);
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

export function fetchProfile(): Promise<ProfileResponse> {
  return request<ProfileResponse>("/profile");
}
