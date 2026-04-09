/// <reference path="./types/index.d.ts" />

interface IAppOption extends WechatMiniprogram.IAnyObject {
  globalData: {
    apiBaseUrl: string;
    userId: string;
    lastAssessmentId?: string;
  };
}
