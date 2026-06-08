const api = require('../../utils/api');

Page({
  data: {
    champion: null,
    championKey: '',
    levels: [3, 7, 11, 15],
    currentLevel: 7,
    available: [],       // 用户点选的3个海克斯
    selected: [],        // 之前已经选过的海克斯
    allAugments: [],     // 该英雄所有海克斯（带胜率）
    filteredAugments: [], // 搜索过滤后的列表
    searchText: '',
    result: null,
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
      const augments = (data.all_augments || data.top_augments || []).map(a => ({
        name: a.name,
        winrate: a.winrate || '',
        tier: a.tier || '',
        pickrate: a.pickrate || '',
        _selected: false,
        _isPrevious: false,
      }));

      // 标记已选过的
      const selected = this.data.selected;
      augments.forEach(a => {
        if (selected.includes(a.name)) {
          a._isPrevious = true;
        }
      });

      this.setData({
        champion: {
          name: data.name,
          tier: data.tier,
          winrate: data.winrate,
          image_url: data.images?.icon || '',
        },
        allAugments: augments,
      });
      this.filterAugments();
    } catch (e) {
      console.error('Load champion failed:', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  onLevelTap(e) {
    this.setData({ currentLevel: e.currentTarget.dataset.level });
  },

  onSearch(e) {
    this.setData({ searchText: e.detail.value });
    this.filterAugments();
  },

  filterAugments() {
    const { allAugments, searchText } = this.data;
    let result = allAugments;
    if (searchText) {
      const s = searchText.toLowerCase();
      result = result.filter(a => a.name.toLowerCase().includes(s));
    }
    this.setData({ filteredAugments: result });
  },

  onAugmentTap(e) {
    const name = e.currentTarget.dataset.name;
    const { available, allAugments, selected } = this.data;

    // 已选过的不能点
    if (selected.includes(name)) {
      wx.showToast({ title: '该海克斯已选过', icon: 'none' });
      return;
    }

    let newAvailable;
    if (available.includes(name)) {
      // 取消选择
      newAvailable = available.filter(n => n !== name);
    } else {
      if (available.length >= 3) {
        wx.showToast({ title: '最多选3个', icon: 'none' });
        return;
      }
      newAvailable = [...available, name];
    }

    // 更新列表的选中状态
    const updated = allAugments.map(a => ({
      ...a,
      _selected: newAvailable.includes(a.name),
    }));

    this.setData({
      available: newAvailable,
      allAugments: updated,
    });
    this.filterAugments();

    // 选满3个自动推荐
    if (newAvailable.length === 3) {
      this.getRecommendation(newAvailable);
    } else {
      this.setData({ result: null });
    }
  },

  onRemoveSelected(e) {
    const idx = e.currentTarget.dataset.index;
    const selected = this.data.selected.filter((_, i) => i !== idx);
    this.setData({ selected });
    wx.setStorageSync('selected_augments', JSON.stringify(selected));

    // 更新列表标记
    const updated = this.data.allAugments.map(a => ({
      ...a,
      _isPrevious: selected.includes(a.name),
    }));
    this.setData({ allAugments: updated });
    this.filterAugments();
  },

  async getRecommendation(available) {
    const { championKey, currentLevel, selected } = this.data;

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

      // 推荐后自动加入已选列表
      if (result.recommendation) {
        const newSelected = [...selected, result.recommendation];
        this.setData({ selected: newSelected });
        wx.setStorageSync('selected_augments', JSON.stringify(newSelected));

        // 更新列表
        const updated = this.data.allAugments.map(a => ({
          ...a,
          _selected: false,
          _isPrevious: newSelected.includes(a.name),
        }));
        this.setData({
          allAugments: updated,
          available: [],
        });
        this.filterAugments();
      }

      this.setData({ result });

      // 3秒后清除推荐栏（用户已看到）
      setTimeout(() => {
        this.setData({ result: null });
      }, 5000);
    } catch (e) {
      console.error('Recommend failed:', e);
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
