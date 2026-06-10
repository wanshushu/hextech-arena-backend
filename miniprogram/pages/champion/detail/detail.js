const api = require('../../../utils/api');

const TIER_COLORS = {
  T1: '#FF3366',
  T2: '#FFA94D',
  T3: '#FFE066',
  T4: '#69DB7C',
  T5: '#74C0FC',
};

const FAVORITES_KEY = 'favorite_champions';

Page({
  data: {
    champion: null,
    loading: true,
    tierColor: '#888',
    skillKeys: ['Q', 'W', 'E', 'R'],
    isFavorite: false,
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
      const isFavorite = this.checkFavorite(data.key || key);

      this.setData({
        champion: data,
        loading: false,
        tierColor: TIER_COLORS[data.tier] || '#888',
        isFavorite,
      });

      wx.setNavigationBarTitle({ title: data.name });

      // 添加导航栏收藏按钮
      wx.setMenuAction({
        menuList: [{ text: isFavorite ? '取消收藏' : '收藏' }],
      });
    } catch (e) {
      console.error('Load champion failed:', e);
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  checkFavorite(key) {
    try {
      const favs = wx.getStorageSync(FAVORITES_KEY);
      const list = favs ? JSON.parse(favs) : [];
      return list.includes(String(key));
    } catch (e) {
      return false;
    }
  },

  toggleFavorite() {
    const { champion, isFavorite } = this.data;
    if (!champion) return;

    const key = String(champion.key);
    try {
      let favs = wx.getStorageSync(FAVORITES_KEY);
      let list = favs ? JSON.parse(favs) : [];

      if (isFavorite) {
        list = list.filter(k => k !== key);
        wx.showToast({ title: '已取消收藏', icon: 'none' });
      } else {
        list.push(key);
        wx.showToast({ title: '已收藏', icon: 'success' });
      }

      wx.setStorageSync(FAVORITES_KEY, JSON.stringify(list));
      this.setData({ isFavorite: !isFavorite });
    } catch (e) {
      console.error('Toggle favorite failed:', e);
    }
  },

  goAugment() {
    const key = this.data.champion?.key;
    if (key) {
      wx.navigateTo({ url: `/pages/augment/augment?key=${key}` });
    }
  },

  goQuick() {
    const key = this.data.champion?.key;
    if (key) {
      wx.navigateTo({ url: `/pages/quick/quick?key=${key}` });
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
