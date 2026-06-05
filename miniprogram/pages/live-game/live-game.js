const api = require('../../utils/api');

const HISTORY_KEY = 'live_game_history';

Page({
  data: {
    summonerName: '',
    tagLine: 'KR1',
    querying: false,
    result: null,
    blueTeam: [],
    redTeam: [],
    expandedKey: null,
    error: '',
    history: [],
  },

  onLoad() {
    this.loadHistory();
  },

  loadHistory() {
    try {
      const raw = wx.getStorageSync(HISTORY_KEY);
      if (raw) this.setData({ history: JSON.parse(raw) });
    } catch (e) {}
  },

  saveHistory(name, tag) {
    let history = this.data.history.filter(
      h => !(h.name === name && h.tag === tag)
    );
    history.unshift({ name, tag });
    history = history.slice(0, 5);
    this.setData({ history });
    wx.setStorageSync(HISTORY_KEY, JSON.stringify(history));
  },

  onNameInput(e) {
    this.setData({ summonerName: e.detail.value });
  },

  onTagInput(e) {
    this.setData({ tagLine: e.detail.value });
  },

  onHistoryTap(e) {
    const { name, tag } = e.currentTarget.dataset;
    this.setData({ summonerName: name, tagLine: tag });
    this.onQuery();
  },

  async onQuery() {
    const { summonerName, tagLine } = this.data;
    if (!summonerName.trim()) {
      wx.showToast({ title: '请输入召唤师名', icon: 'none' });
      return;
    }

    this.setData({ querying: true, result: null, error: '', expandedKey: null });

    try {
      const data = await api.getLiveGame(summonerName.trim(), tagLine.trim() || 'KR1');

      if (data.status === 'in_game') {
        // 分蓝红方
        const blueTeam = data.participants.filter(p => p.team_id === 100);
        const redTeam = data.participants.filter(p => p.team_id === 200);
        this.setData({
          result: data,
          blueTeam,
          redTeam,
          querying: false,
        });
      } else {
        this.setData({
          result: data,
          querying: false,
        });
      }

      this.saveHistory(summonerName.trim(), tagLine.trim() || 'KR1');
    } catch (e) {
      console.error('Query failed:', e);
      this.setData({
        error: e.message || '查询失败，请检查召唤师名',
        querying: false,
      });
    }
  },

  onPlayerTap(e) {
    const key = e.currentTarget.dataset.key;
    if (key) {
      // 点击展开/收起详情
      this.setData({
        expandedKey: this.data.expandedKey === key ? null : key,
      });
    }
  },

  onShareAppMessage() {
    return {
      title: '海克斯大乱斗 - 实时对局攻略',
      path: '/pages/live-game/live-game',
    };
  },
});
