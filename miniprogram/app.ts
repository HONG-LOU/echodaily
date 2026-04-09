const defaultApiBaseUrl = "https://template-chat.xyz/api/v1";
const legacyApiBaseUrls = [
  "http://127.0.0.1:8000/api/v1",
  "http://localhost:8000/api/v1",
  "http://8.156.77.141/api/v1",
  "https://8.156.77.141/api/v1",
  "http://template-chat.xyz/api/v1",
];

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
    apiBaseUrl: defaultApiBaseUrl,
    userId: "",
    accessToken: "",
    tokenExpiresAt: "",
    lastAssessmentId: "",
  },
  onLaunch() {
    const envVersion = getEnvVersion();
    const savedApiBaseUrl = normalizeApiBaseUrl(wx.getStorageSync("apiBaseUrl"));
    if (envVersion !== "develop") {
      this.globalData.apiBaseUrl = defaultApiBaseUrl;
      wx.setStorageSync("apiBaseUrl", defaultApiBaseUrl);
    } else if (savedApiBaseUrl) {
      if (
        legacyApiBaseUrls.includes(savedApiBaseUrl) ||
        !/^https?:\/\//.test(savedApiBaseUrl)
      ) {
        this.globalData.apiBaseUrl = defaultApiBaseUrl;
        wx.setStorageSync("apiBaseUrl", defaultApiBaseUrl);
      } else {
        this.globalData.apiBaseUrl = savedApiBaseUrl;
      }
    } else {
      wx.setStorageSync("apiBaseUrl", defaultApiBaseUrl);
    }

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
