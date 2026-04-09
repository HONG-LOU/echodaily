const defaultApiBaseUrl = "https://template-chat.xyz/api/v1";

App<IAppOption>({
  globalData: {
    apiBaseUrl: defaultApiBaseUrl,
    userId: "",
    accessToken: "",
    tokenExpiresAt: "",
    lastAssessmentId: "",
  },
  onLaunch() {
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
