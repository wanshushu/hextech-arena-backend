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
        // 提取有意义的属性 key
        const statsKeys = Object.keys(item.stats || {});
        return { ...item, statsKeys };
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
