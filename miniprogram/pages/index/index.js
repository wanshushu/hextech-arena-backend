const api = require('../../utils/api');

const FAVORITES_KEY = 'favorite_champions';

Page({
  data: {
    tiers: [
      { name: 'all', label: '全部' },
      { name: 'fav', label: '⭐' },
      { name: 'T1' },
      { name: 'T2' },
      { name: 'T3' },
      { name: 'T4' },
      { name: 'T5' },
    ],
    currentTier: 'all',
    searchText: '',
    allChampions: [],
    filteredChampions: [],
    updateTime: '',
    loading: true,
    favorites: [],
  },

  onLoad() {
    this.loadFavorites();
    this.loadData();
  },

  onShow() {
    // 每次进入页面刷新收藏（可能从详情页修改了）
    this.loadFavorites();
    this.filterChampions();
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh());
  },

  loadFavorites() {
    try {
      const favs = wx.getStorageSync(FAVORITES_KEY);
      this.setData({ favorites: favs ? JSON.parse(favs) : [] });
    } catch (e) {}
  },

  saveFavorites(favs) {
    this.setData({ favorites: favs });
    wx.setStorageSync(FAVORITES_KEY, JSON.stringify(favs));
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      // 检查缓存
      const cacheKey = 'tier_list_cache';
      const cached = wx.getStorageSync(cacheKey);
      let tierData, ddData;

      if (cached) {
        const parsed = JSON.parse(cached);
        // 缓存 30 分钟有效
        if (Date.now() - parsed.ts < 30 * 60 * 1000) {
          tierData = parsed.tierData;
          ddData = parsed.ddData;
        }
      }

      if (!tierData) {
        [tierData, ddData] = await Promise.all([
          api.getTierList(),
          api.getChampions(),
        ]);
        // 存缓存
        wx.setStorageSync(cacheKey, JSON.stringify({
          ts: Date.now(),
          tierData,
          ddData,
        }));
      }

      // 建立 id → ddragon 数据的映射
      const ddMap = {};
      (ddData.champions || []).forEach(c => {
        ddMap[c.id] = c;
        ddMap[c.key] = c;
      });

      const allChampions = [];
      for (const tier of ['T1', 'T2', 'T3', 'T4', 'T5']) {
        const champs = tierData.tiers[tier] || [];
        champs.forEach(c => {
          c.tier = tier;
          const dd = ddMap[c.id] || ddMap[String(c.id)];
          if (dd) {
            c.image_url = dd.image_url;
            c.key = dd.key;
          }
          allChampions.push(c);
        });
      }

      getApp().globalData.champions = ddData.champions;

      let updateTime = '';
      if (tierData.updated_at) {
        const d = new Date(tierData.updated_at);
        updateTime = `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      }

      this.setData({ allChampions, updateTime, loading: false });
      this.filterChampions();
    } catch (e) {
      console.error('Load failed:', e);
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onTabTap(e) {
    const tier = e.currentTarget.dataset.tier;
    this.setData({ currentTier: tier });
    this.filterChampions();
  },

  goCompare() {
    wx.navigateTo({ url: '/pages/compare/compare' });
  },

  onSearch(e) {
    this.setData({ searchText: e.detail.value });
    this.filterChampions();
  },

  filterChampions() {
    const { allChampions, currentTier, searchText, favorites } = this.data;
    let result = allChampions;

    if (currentTier === 'fav') {
      result = result.filter(c => favorites.includes(c.key || c.id));
    } else if (currentTier !== 'all') {
      result = result.filter(c => c.tier === currentTier);
    }

    if (searchText) {
      const s = searchText.toLowerCase();
      result = result.filter(c =>
        c.name.toLowerCase().includes(s) ||
        (c.title && c.title.toLowerCase().includes(s))
      );
    }

    this.setData({ filteredChampions: result });
  },
});
