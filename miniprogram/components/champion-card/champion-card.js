Component({
  properties: {
    champion: {
      type: Object,
      value: {},
    },
  },
  methods: {
    onTap() {
      const key = this.data.champion.key || this.data.champion.id;
      wx.navigateTo({
        url: `/pages/champion/detail/detail?key=${key}`,
      });
    },
  },
});
