const api = require('../../utils/api');

Page({
  data: {
    tiers: [
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
  },

  onLoad() {
    this.loadData();
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh());
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      // 同时加载梯度表和 Data Dragon 英雄数据
      const [tierData, ddData] = await Promise.all([
        api.getTierList(),
        api.getChampions(),
      ]);

      // 建立 id → ddragon 数据的映射
      const ddMap = {};
      (ddData.champions || []).forEach(c => {
        ddMap[c.id] = c;   // id: "Aatrox"
        ddMap[c.key] = c;   // key: "266"
      });

      const allChampions = [];

      for (const tier of ['T1', 'T2', 'T3', 'T4', 'T5']) {
        const champs = tierData.tiers[tier] || [];
        champs.forEach(c => {
          c.tier = tier;
          // 用 id 或 key 去匹配 ddragon 数据
          const dd = ddMap[c.id] || ddMap[String(c.id)];
          if (dd) {
            c.image_url = dd.image_url;
            c.key = dd.key;
          }
          allChampions.push(c);
        });
      }

      // 缓存到全局
      getApp().globalData.champions = ddData.champions;

      let updateTime = '';
      if (tierData.updated_at) {
        const d = new Date(tierData.updated_at);
        updateTime = `${d.getMonth() + 1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
      }

      this.setData({
        allChampions,
        updateTime,
        loading: false,
      });
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

  onSearch(e) {
    this.setData({ searchText: e.detail.value });
    this.filterChampions();
  },

  filterChampions() {
    const { allChampions, currentTier, searchText } = this.data;
    let result = allChampions;

    if (currentTier !== 'all') {
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
