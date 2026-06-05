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
      const data = await api.getTierList();
      const allChampions = [];

      // 合并所有梯度
      for (const tier of ['T1', 'T2', 'T3', 'T4', 'T5']) {
        const champs = data.tiers[tier] || [];
        champs.forEach(c => {
          c.tier = tier;
          // 尝试从预加载数据中补充 image_url
          const cached = this._findCachedChamp(c.id);
          if (cached) {
            c.image_url = cached.image_url;
            c.key = cached.key;
          }
          allChampions.push(c);
        });
      }

      // 格式化时间
      let updateTime = '';
      if (data.updated_at) {
        const d = new Date(data.updated_at);
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

  _findCachedChamp(id) {
    const champs = getApp().globalData.champions;
    if (!champs) return null;
    return champs.find(c => c.id === id || c.key === String(id));
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
