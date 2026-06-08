const api = require('../../utils/api');

Page({
  data: {
    allItems: [],
    filteredItems: [],
    searchText: '',
    sortBy: 'price',
    loading: true,
  },

  onLoad() {
    this.loadItems();
  },

  onPullDownRefresh() {
    this.loadItems().then(() => wx.stopPullDownRefresh());
  },

  async loadItems() {
    this.setData({ loading: true });
    try {
      const data = await api.getItems();
      const items = (data.items || []).map(item => {
        const stats = item.stats || {};
        // 格式化属性显示
        const statsText = Object.entries(stats)
          .map(([k, v]) => {
            if (typeof v === 'number' && v < 1 && v > 0) {
              return `${k} ${Math.round(v * 100)}%`;
            }
            return `${k} +${v}`;
          })
          .join(' | ');
        return { ...item, statsText };
      });
      this.setData({ allItems: items, loading: false });
      this.filterAndSort();
    } catch (e) {
      console.error('Load items failed:', e);
      this.setData({ loading: false });
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onSearch(e) {
    this.setData({ searchText: e.detail.value });
    this.filterAndSort();
  },

  onSort(e) {
    this.setData({ sortBy: e.currentTarget.dataset.sort });
    this.filterAndSort();
  },

  filterAndSort() {
    const { allItems, searchText, sortBy } = this.data;
    let result = allItems;

    if (searchText) {
      const s = searchText.toLowerCase();
      result = result.filter(i => i.name.toLowerCase().includes(s));
    }

    if (sortBy === 'price') {
      result.sort((a, b) => b.gold_total - a.gold_total);
    } else {
      result.sort((a, b) => a.name.localeCompare(b.name));
    }

    // 只显示前 100 个，避免卡顿
    this.setData({ filteredItems: result.slice(0, 100) });
  },
});
