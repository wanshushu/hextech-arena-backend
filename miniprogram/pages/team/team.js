const api = require('../../utils/api');

// 英雄名字缓存
let championNames = [];

Page({
  data: {
    imagePath: '',
    ocrStatus: '',
    recognizedNames: [],
    result: null,
  },

  onLoad() {
    this.loadChampionNames();
  },

  async loadChampionNames() {
    try {
      const data = await api.request('/team/champion-names');
      championNames = data.names || [];
    } catch (e) {
      console.warn('Load champion names failed:', e);
    }
  },

  // 拍照
  onCapture() {
    this.chooseImage('camera');
  },

  // 从相册选
  onPickImage() {
    this.chooseImage('album');
  },

  chooseImage(sourceType) {
    wx.chooseMedia({
      count: 1,
      mediaType: ['image'],
      sourceType: [sourceType],
      success: (res) => {
        const path = res.tempFiles[0].tempFilePath;
        this.setData({ imagePath: path, ocrStatus: '正在识别...', result: null });
        this.doOCR(path);
      },
    });
  },

  async doOCR(imagePath) {
    try {
      // 读取图片为 base64
      const fs = wx.getFileSystemManager();
      const base64 = fs.readFileSync(imagePath, 'base64');

      // 先尝试用微信 OCR 插件（如果可用）
      let ocrText = '';

      // 方案1：使用小程序 OCR 插件
      // 需要在 app.json 中声明插件，这里先用后端方案
      try {
        // 发送到后端做 OCR
        // 由于后端暂无 OCR 库，先用前端方案
        ocrText = await this.tryFrontendOCR(base64);
      } catch (e) {
        console.warn('Frontend OCR failed:', e);
      }

      if (!ocrText) {
        this.setData({ ocrStatus: '识别失败，请手动输入' });
        return;
      }

      // 匹配英雄名字
      const matched = this.matchChampionNames(ocrText);

      if (matched.length === 0) {
        this.setData({ ocrStatus: '未识别到英雄，请手动输入' });
      } else {
        this.setData({
          recognizedNames: matched,
          ocrStatus: `识别到 ${matched.length} 个英雄`,
        });
      }
    } catch (e) {
      console.error('OCR failed:', e);
      this.setData({ ocrStatus: '识别出错，请手动输入' });
    }
  },

  // 前端 OCR（尝试用 wx.recognizeText）
  tryFrontendOCR(base64) {
    return new Promise((resolve, reject) => {
      // wx.recognizeText 需要基础库 2.25.0+
      if (wx.recognizeText) {
        wx.recognizeText({
          imgUrl: 'data:image/jpeg;base64,' + base64,
          success: (res) => {
            resolve(res.text || '');
          },
          fail: reject,
        });
      } else {
        reject(new Error('wx.recognizeText not available'));
      }
    });
  },

  // 从 OCR 文本中匹配英雄名字
  matchChampionNames(text) {
    if (!championNames.length) return [];

    // 按名字长度排序（长的优先匹配）
    const sorted = [...championNames].sort((a, b) => b.name.length - a.name.length);

    const matched = [];
    let remaining = text;

    for (const champ of sorted) {
      if (remaining.includes(champ.name)) {
        matched.push(champ.name);
        remaining = remaining.replace(champ.name, ' ');
        if (matched.length >= 10) break;
      }
    }

    return matched;
  },

  // 移除识别错误的英雄
  onRemoveName(e) {
    const idx = e.currentTarget.dataset.index;
    const names = this.data.recognizedNames.filter((_, i) => i !== idx);
    this.setData({ recognizedNames: names });
  },

  // 手动输入
  onManualInput() {
    wx.showModal({
      title: '手动输入英雄名',
      content: '用逗号分隔多个英雄名，如：暗裔剑魔,复仇焰魂,荆棘之兴',
      editable: true,
      placeholderText: '暗裔剑魔,复仇焰魂,荆棘之兴',
      success: (res) => {
        if (res.confirm && res.content) {
          const names = res.content.split(/[,，、\s]+/).filter(Boolean);
          this.setData({ recognizedNames: names });
        }
      },
    });
  },

  // 分析
  async onAnalyze() {
    const names = this.data.recognizedNames;
    if (names.length === 0) {
      wx.showToast({ title: '请先识别英雄', icon: 'none' });
      return;
    }

    wx.showLoading({ title: '分析中...' });

    try {
      const result = await api.request('/team/analyze-by-names', {
        method: 'POST',
        data: { names },
      });
      this.setData({ result });
      wx.hideLoading();
    } catch (e) {
      wx.hideLoading();
      wx.showToast({ title: '分析失败', icon: 'none' });
    }
  },

  onShareAppMessage() {
    return {
      title: '海克斯大乱斗 - 队伍组合分析',
      path: '/pages/team/team',
    };
  },
});
