const api = require('../../utils/api');

const FAVORITES_KEY = 'favorite_champions';

// 常用英雄别名（玩家常用称呼 → 英雄名）
const ALIASES = {
  '卡牌': '崔斯特', '卡牌大师': '崔斯特',
  '盲僧': '李青', '瞎子': '李青',
  '石头人': '墨菲特', '石头': '墨菲特',
  '寒冰': '艾希', '寒冰射手': '艾希',
  '火男': '布兰德', '火女': '安妮',
  '蛮王': '泰达米尔', '蛮子': '泰达米尔',
  '剑圣': '易', '无极剑圣': '易',
  '狗头': '内瑟斯', '狗头人': '内瑟斯',
  '鳄鱼': '雷克顿',
  '薇恩': '维恩', 'VN': '维恩', 'vn': '维恩',
  '瑞文': '锐雯', '放逐之刃': '锐雯',
  '劫': '劫', '影流之主': '劫',
  '亚索': '亚索', '快乐风男': '亚索',
  '永恩': '永恩',
  'EZ': '伊泽瑞尔', 'ez': '伊泽瑞尔', '探险家': '伊泽瑞尔',
  '诺手': '德莱厄斯', '诺克': '德莱厄斯',
  '盖伦': '盖伦', '德玛': '盖伦', '德玛西亚之力': '盖伦',
  '提莫': '提莫', '迅捷斥候': '提莫',
  '机器人': '布里茨', '锤石': '锤石',
  '风女': '迦娜', '娜美': '娜美',
  '大嘴': '克格莫', '老鼠': '图奇',
  '小鱼人': '菲兹', '鱼人': '菲兹',
  '冰女': '丽桑卓', '冰鸟': '艾尼维亚',
  '酒桶': '古拉加斯', '皇子': '嘉文四世',
  '猪妹': '瑟庄妮', '龙女': '希瓦娜',
  '螳螂': '卡兹克', '狮子狗': '雷恩加尔',
  '蜘蛛': '伊莉丝', '寡妇': '伊芙琳',
  '阿卡丽': '阿卡丽', '离群之刺': '阿卡丽',
  '塞拉斯': '塞拉斯', '解脱者': '塞拉斯',
};

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
      // 别名匹配：把别名转成正式名再搜索
      const aliasMatch = ALIASES[s] || ALIASES[s.toUpperCase()] || '';
      result = result.filter(c =>
        c.name.toLowerCase().includes(s) ||
        (c.title && c.title.toLowerCase().includes(s)) ||
        (aliasMatch && c.name.includes(aliasMatch))
      );
    }

    this.setData({ filteredChampions: result });
  },
});
