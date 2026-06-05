/**
 * API 工具封装
 */
const app = getApp();

/**
 * 封装 wx.request 为 Promise
 */
function request(path, options = {}) {
  return app.request(path, options);
}

/**
 * 获取梯度表
 */
function getTierList() {
  return request('/tier-list');
}

/**
 * 获取合并版英雄详情
 */
function getChampionDetail(key) {
  return request(`/ddragon/champions/${key}`);
}

/**
 * 获取所有英雄
 */
function getChampions() {
  return request('/ddragon/champions');
}

/**
 * 装备列表
 */
function getItems(search) {
  const path = search ? `/ddragon/items?search=${encodeURIComponent(search)}` : '/ddragon/items';
  return request(path);
}

/**
 * 符文树
 */
function getRunes() {
  return request('/ddragon/runes');
}

/**
 * 实时对局查询
 */
function getLiveGame(name, tag) {
  return request(`/riot/live-game/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`);
}

/**
 * 召唤师查询
 */
function getSummoner(name, tag) {
  return request(`/riot/summoner/${encodeURIComponent(name)}/${encodeURIComponent(tag)}`);
}

/**
 * 获取英雄头像 URL
 */
function getChampionIcon(key) {
  // 从预加载的数据中取
  const champs = app.globalData.champions;
  if (champs) {
    const found = champs.find(c => c.key === String(key));
    if (found) return found.image_url;
  }
  // fallback：用 Data Dragon 直接拼
  return `https://ddragon.leagueoflegends.com/cdn/16.11.1/img/champion/${key}.png`;
}

module.exports = {
  request,
  getTierList,
  getChampionDetail,
  getChampions,
  getItems,
  getRunes,
  getLiveGame,
  getSummoner,
  getChampionIcon,
};
