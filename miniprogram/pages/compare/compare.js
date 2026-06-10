const api = require('../../utils/api');

const TIER_SCORE = { T1: 5, T2: 4, T3: 3, T4: 2, T5: 1 };

Page({
  data: {
    champ1: null,
    champ2: null,
    conclusion: '',
    showPicker: false,
    pickerSlot: 1,
    pickerSearch: '',
    pickerList: [],
    allChamps: [],
  },

  onLoad() {
    this.loadChamps();
  },

  async loadChamps() {
    try {
      const data = await api.getChampions();
      this.setData({ allChamps: data.champions || [], pickerList: data.champions || [] });
    } catch (e) {
      console.error('Load champs failed:', e);
    }
  },

  onSelectChamp(e) {
    const slot = e.currentTarget.dataset.slot;
    this.setData({ showPicker: true, pickerSlot: slot, pickerSearch: '' });
    this.setData({ pickerList: this.data.allChamps });
  },

  onClosePicker() {
    this.setData({ showPicker: false });
  },

  onPickerSearch(e) {
    const s = e.detail.value.toLowerCase();
    const list = this.data.allChamps.filter(c =>
      c.name.toLowerCase().includes(s)
    );
    this.setData({ pickerList: list, pickerSearch: e.detail.value });
  },

  async onPickChamp(e) {
    const { key, name, image } = e.currentTarget.dataset;
    const slot = this.data.pickerSlot;

    // 立即关闭面板，防止重复触发
    this.setData({ showPicker: false });

    try {
      const data = await api.getChampionDetail(key);
      const champ = {
        ...data,
        image_url: image,
        _wrColor: this.getWinrateColor(data.winrate),
      };

      if (slot === 1) {
        this.setData({ champ1: champ });
      } else {
        this.setData({ champ2: champ });
      }

      // 两个都有了就生成结论
      if ((slot === 1 && this.data.champ2) || (slot === 2 && this.data.champ1)) {
        this.generateConclusion();
      }
    } catch (e) {
      console.error('Load champion failed:', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  getWinrateColor(wrStr) {
    const wr = parseFloat(wrStr) || 0;
    if (wr >= 54) return '#00ff88';
    if (wr >= 52) return '#69DB7C';
    if (wr >= 50) return '#FFE066';
    if (wr >= 48) return '#FFA94D';
    return '#FF3366';
  },

  generateConclusion() {
    const { champ1, champ2 } = this.data;
    if (!champ1 || !champ2) return;

    const score1 = (TIER_SCORE[champ1.tier] || 1) + (parseFloat(champ1.winrate) || 50) / 20;
    const score2 = (TIER_SCORE[champ2.tier] || 1) + (parseFloat(champ2.winrate) || 50) / 20;

    let conclusion = '';
    const diff = Math.abs(score1 - score2);
    const winner = score1 > score2 ? champ1 : champ2;
    const loser = score1 > score2 ? champ2 : champ1;

    if (diff < 0.3) {
      conclusion = `两者实力接近，按喜好选择即可`;
    } else if (diff < 1) {
      conclusion = `${winner.name} 略优于 ${loser.name}`;
    } else {
      conclusion = `${winner.name} 明显优于 ${loser.name}，建议优先选择`;
    }

    this.setData({ conclusion });
  },

  onShareAppMessage() {
    return {
      title: '海克斯大乱斗 - 英雄对比',
      path: '/pages/compare/compare',
    };
  },
});
