const api = require('../../../utils/api');

const TIER_COLORS = {
  T1: '#FF3366',
  T2: '#FFA94D',
  T3: '#FFE066',
  T4: '#69DB7C',
  T5: '#74C0FC',
};

Page({
  data: {
    champion: null,
    loading: true,
    tierColor: '#888',
    skillKeys: ['Q', 'W', 'E', 'R'],
  },

  onLoad(options) {
    const key = options.key;
    if (key) {
      this.loadChampion(key);
    }
  },

  async loadChampion(key) {
    this.setData({ loading: true });
    try {
      const data = await api.getChampionDetail(key);
      this.setData({
        champion: data,
        loading: false,
        tierColor: TIER_COLORS[data.tier] || '#888',
      });

      // 更新导航栏标题
      wx.setNavigationBarTitle({ title: data.name });
    } catch (e) {
      console.error('Load champion failed:', e);
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onShareAppMessage() {
    const c = this.data.champion;
    return {
      title: `${c.name} - ${c.tier} | 胜率${c.winrate} | 海克斯大乱斗攻略`,
      path: `/pages/champion/detail/detail?key=${c.key}`,
    };
  },
});
