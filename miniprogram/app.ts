const developApiBaseUrl = "http://127.0.0.1:8000/api/v1";
const releaseApiBaseUrl = "https://your-production-domain.example/api/v1";

function normalizeApiBaseUrl(value: unknown): string {
  return String(value || "")
    .trim()
    .replace(/\/$/, "");
}

function getEnvVersion(): "develop" | "trial" | "release" {
  try {
    return wx.getAccountInfoSync().miniProgram.envVersion;
  } catch {
    return "develop";
  }
}

App<IAppOption>({
  globalData: {
    apiBaseUrl: developApiBaseUrl,
    userId: "",
    accessToken: "",
    tokenExpiresAt: "",
    lastAssessmentId: "",
  },
  onLaunch() {
    const envVersion = getEnvVersion();
    const defaultApiBaseUrl =
      envVersion === "develop" ? developApiBaseUrl : releaseApiBaseUrl;

    this.globalData.apiBaseUrl = defaultApiBaseUrl;
    wx.setStorageSync("apiBaseUrl", defaultApiBaseUrl);

    const savedUserId = wx.getStorageSync("userId");
    if (savedUserId && typeof savedUserId === "string") {
      this.globalData.userId = savedUserId;
    }

    const savedAccessToken = wx.getStorageSync("accessToken");
    if (savedAccessToken && typeof savedAccessToken === "string") {
      this.globalData.accessToken = savedAccessToken;
    }

    const savedTokenExpiresAt = wx.getStorageSync("tokenExpiresAt");
    if (savedTokenExpiresAt && typeof savedTokenExpiresAt === "string") {
      this.globalData.tokenExpiresAt = savedTokenExpiresAt;
    }

    wx.showShareMenu({
      menus: ["shareAppMessage", "shareTimeline"],
    });
  },
});
