Component({
  properties: {
    visible: {
      type: Boolean,
      value: false,
      observer(newVal) {
        if (newVal) {
          setTimeout(() => {
            this.drawPoster();
          }, 100);
        }
      }
    },
    nickname: {
      type: String,
      value: '神秘用户'
    },
    score: {
      type: Number,
      value: 0
    },
    lessonTitle: {
      type: String,
      value: '今日练习'
    },
    streakDays: {
      type: Number,
      value: 0
    }
  },

  data: {
    canvasWidth: 300,
    canvasHeight: 480,
    saving: false,
    tempFilePath: ''
  },

  methods: {
    close() {
      this.setData({ visible: false, tempFilePath: '' });
      this.triggerEvent('close');
    },

    drawPoster() {
      const query = this.createSelectorQuery();
      query.select('#posterCanvas')
        .fields({ node: true, size: true })
        .exec((res) => {
          if (!res[0] || !res[0].node) return;
          
          const canvas = res[0].node;
          const ctx = canvas.getContext('2d');
          const dpr = wx.getSystemInfoSync().pixelRatio;
          
          canvas.width = res[0].width * dpr;
          canvas.height = res[0].height * dpr;
          ctx.scale(dpr, dpr);

          const { canvasWidth: w, canvasHeight: h } = this.data;
          
          // Draw background
          ctx.fillStyle = '#F5F7FA';
          ctx.fillRect(0, 0, w, h);

          // Draw header
          ctx.fillStyle = '#2C3E50';
          ctx.font = 'bold 24px sans-serif';
          ctx.fillText('EchoDaily 每日回音', 20, 40);

          // Draw score
          ctx.fillStyle = '#4A90E2';
          ctx.font = 'bold 64px sans-serif';
          ctx.fillText(`${this.data.score}`, 20, 120);
          ctx.font = '16px sans-serif';
          ctx.fillStyle = '#7F8C8D';
          ctx.fillText('本次得分', 100, 115);

          // Draw lesson title
          ctx.fillStyle = '#2C3E50';
          ctx.font = 'bold 20px sans-serif';
          ctx.fillText(this.data.lessonTitle, 20, 180);

          // Draw user info
          ctx.fillStyle = '#34495E';
          ctx.font = '16px sans-serif';
          ctx.fillText(`@${this.data.nickname}`, 20, 240);
          ctx.fillText(`连续打卡 ${this.data.streakDays} 天`, 20, 270);

          // Draw QR code placeholder
          ctx.fillStyle = '#FFFFFF';
          ctx.fillRect(200, 380, 80, 80);
          ctx.fillStyle = '#BDC3C7';
          ctx.font = '12px sans-serif';
          ctx.fillText('扫码练习', 215, 425);

          // Export to temp file
          setTimeout(() => {
            wx.canvasToTempFilePath({
              canvas,
              success: (res) => {
                this.setData({ tempFilePath: res.tempFilePath });
              },
              fail: (err) => {
                console.error('Failed to export canvas', err);
              }
            });
          }, 500);
        });
    },

    saveToAlbum() {
      if (!this.data.tempFilePath) {
        wx.showToast({ title: '海报生成中，请稍候', icon: 'none' });
        return;
      }

      this.setData({ saving: true });
      wx.saveImageToPhotosAlbum({
        filePath: this.data.tempFilePath,
        success: () => {
          wx.showToast({ title: '已保存到相册', icon: 'success' });
          this.close();
        },
        fail: (err) => {
          if (err.errMsg.includes('auth deny')) {
            wx.showModal({
              title: '提示',
              content: '需要您授权保存相册',
              success: (res) => {
                if (res.confirm) {
                  wx.openSetting();
                }
              }
            });
          } else {
            wx.showToast({ title: '保存失败', icon: 'none' });
          }
        },
        complete: () => {
          this.setData({ saving: false });
        }
      });
    }
  }
});