const api = require('../../utils/api');

// 别名映射（跟首页共用）
const ALIASES = {
  '卡牌': '崔斯特', '卡牌大师': '崔斯特',
  '盲僧': '李青', '瞎子': '李青',
  '石头人': '墨菲特', '石头': '墨菲特',
  '寒冰': '艾希', '寒冰射手': '艾希',
  '火男': '布兰德', '火女': '安妮',
  '蛮王': '泰达米尔', '蛮子': '泰达米尔',
  '剑圣': '易', '无极剑圣': '易',
  '狗头': '内瑟斯', '鳄鱼': '雷克顿',
  '薇恩': '维恩', 'VN': '维恩', 'vn': '维恩',
  '瑞文': '锐雯',
  'EZ': '伊泽瑞尔', 'ez': '伊泽瑞尔',
  '诺手': '德莱厄斯', '德玛': '盖伦',
  '小鱼人': '菲兹', '鱼人': '菲兹',
  '冰女': '丽桑卓', '酒桶': '古拉加斯',
  '皇子': '嘉文四世', '猪妹': '瑟庄妮',
  '螳螂': '卡兹克', '狮子狗': '雷恩加尔',
};

Page({
  data: {
    champion: null,
    augments: [],
    coreItems: [],
    startItems: [],
    situItems: [],
    showSitu: false,
    switchText: '',
  },

  onLoad(options) {
    const key = options.key;
    if (key) {
      this.loadChampion(key);
    }
  },

  async loadChampion(key) {
    try {
      const data = await api.getChampionDetail(key);
      const augments = (data.top_augments || []).slice(0, 5);

      this.setData({
        champion: {
          name: data.name,
          tier: data.tier,
          winrate: data.winrate,
          image_url: data.images?.icon || '',
          image_splash: data.images?.splash || '',
        },
        augments,
        coreItems: (data.core_items || []).slice(0, 3),
        startItems: data.starting_items || [],
        situItems: data.situational_items || [],
        showSitu: false,
      });

      wx.setNavigationBarTitle({ title: `速查 · ${data.name}` });
    } catch (e) {
      console.error('Load failed:', e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    }
  },

  toggleSitu() {
    this.setData({ showSitu: !this.data.showSitu });
  },

  onSwitchInput(e) {
    this.setData({ switchText: e.detail.value });
  },

  onSwitchConfirm(e) {
    let name = e.detail.value.trim();
    if (!name) return;

    // 别名转换
    const alias = ALIASES[name] || ALIASES[name.toUpperCase()];
    if (alias) name = alias;

    // 从全局数据中找英雄
    const champs = getApp().globalData.champions || [];
    const found = champs.find(c =>
      c.name === name || c.name.includes(name)
    );

    if (found) {
      this.loadChampion(found.key);
      this.setData({ switchText: '' });
    } else {
      wx.showToast({ title: '未找到英雄', icon: 'none' });
    }
  },

  onShareAppMessage() {
    return {
      title: `${this.data.champion?.name || ''} 速查攻略`,
      path: `/pages/quick/quick?key=${this.data.champion?.key}`,
    };
  },
});
