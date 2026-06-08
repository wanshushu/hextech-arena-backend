const api = require('../../utils/api');

Page({
  data: {
    champion: null,
    championKey: '',
    levels: [3, 7, 11, 15],
    currentLevel: 7,
    aug1: '',
    aug2: '',
    aug3: '',
    selected: [],
    newSelected: '',
    result: null,
    loading: false,
  },

  onLoad(options) {
    const key = options.key;
    if (key) {
      this.setData({ championKey: key });
      this.loadChampion(key);
    }
    // 加载已保存的已选海克斯
    const saved = wx.getStorageSync('selected_augments');
    if (saved) {
      this.setData({ selected: JSON.parse(saved) });
    }
  },

  async loadChampion(key) {
    try {
      const data = await api.getChampionDetail(key);
      this.setData({
        champion: {
          name: data.name,
          tier: data.tier,
          image_url: data.images?.icon || '',
        },
      });
    } catch (e) {
      console.error('Load champion failed:', e);
    }
  },

  onLevelTap(e) {
    this.setData({ currentLevel: e.currentTarget.dataset.level });
  },

  onAug1Input(e) { this.setData({ aug1: e.detail.value }); },
  onAug2Input(e) { this.setData({ aug2: e.detail.value }); },
  onAug3Input(e) { this.setData({ aug3: e.detail.value }); },
  onNewSelectedInput(e) { this.setData({ newSelected: e.detail.value }); },

  onAddSelected() {
    const name = this.data.newSelected.trim();
    if (!name) return;
    const selected = [...this.data.selected, name];
    this.setData({ selected, newSelected: '' });
    wx.setStorageSync('selected_augments', JSON.stringify(selected));
  },

  onRemoveSelected(e) {
    const idx = e.currentTarget.dataset.index;
    const selected = this.data.selected.filter((_, i) => i !== idx);
    this.setData({ selected });
    wx.setStorageSync('selected_augments', JSON.stringify(selected));
  },

  async onRecommend() {
    const { championKey, currentLevel, aug1, aug2, aug3, selected } = this.data;
    const available = [aug1.trim(), aug2.trim(), aug3.trim()].filter(Boolean);

    if (!championKey) {
      wx.showToast({ title: '请先选择英雄', icon: 'none' });
      return;
    }
    if (available.length < 2) {
      wx.showToast({ title: '至少输入2个海克斯', icon: 'none' });
      return;
    }

    this.setData({ loading: true, result: null });

    try {
      const result = await api.request('/augment/recommend', {
        method: 'POST',
        data: {
          champion_key: championKey,
          level: currentLevel,
          available: available,
          selected: selected,
        },
      });
      this.setData({ result, loading: false });
    } catch (e) {
      console.error('Recommend failed:', e);
      this.setData({ loading: false });
      wx.showToast({ title: '推荐失败', icon: 'none' });
    }
  },

  onShareAppMessage() {
    return {
      title: '海克斯大乱斗 - 海克斯推荐',
      path: `/pages/augment/augment?key=${this.data.championKey}`,
    };
  },
});
