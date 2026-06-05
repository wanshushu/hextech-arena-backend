App({
  globalData: {
    // API 地址（开发时用本地，上线后切 Railway）
    apiBase: 'https://web-production-fa0e7.up.railway.app',
    // 开发时可切换为：
    // apiBase: 'http://127.0.0.1:8000',

    // 缓存的英雄数据
    champions: null,
    tierList: null,
  },

  onLaunch() {
    // 预加载英雄数据
    this.preloadData();
  },

  async preloadData() {
    try {
      const res = await this.request('/ddragon/champions');
      this.globalData.champions = res.champions;
    } catch (e) {
      console.warn('Preload champions failed:', e);
    }
  },

  // 封装请求方法
  request(path, options = {}) {
    return new Promise((resolve, reject) => {
      wx.request({
        url: this.globalData.apiBase + path,
        method: options.method || 'GET',
        data: options.data || {},
        header: {
          'Content-Type': 'application/json',
          ...options.header,
        },
        success(res) {
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(res.data);
          } else {
            reject(new Error(res.data?.detail || `HTTP ${res.statusCode}`));
          }
        },
        fail(err) {
          reject(err);
        },
      });
    });
  },
});
