// pages/index/index.js — 首页
const app = getApp();

Page({
  data: {
    banners: [],
    categories: [],
    products: [],
    keyword: '',
    cartCount: 0
  },

  onLoad() {
    this.loadData();
    this.setData({ cartCount: app.globalData.cartCount });
  },

  onShow() {
    this.setData({ cartCount: app.globalData.cartCount });
  },

  loadData() {
    // banners — 可从后端/api加载，这里用模拟数据
    this.setData({
      banners: [
        { id: 1, image: 'https://via.placeholder.com/750x300/ff6b35/fff?text=新品上市' },
        { id: 2, image: 'https://via.placeholder.com/750x300/2ecc71/fff?text=限时特惠' },
        { id: 3, image: 'https://via.placeholder.com/750x300/3498db/fff?text=会员专享' }
      ],
      categories: [
        { name: '热销', icon: '🔥' },
        { name: '新品', icon: '✨' },
        { name: '特价', icon: '💎' },
        { name: '推荐', icon: '🎯' }
      ],
      products: [
        { id: 1, name: '商品名称示例1', price: 29.90, originalPrice: 59.00, image: 'https://via.placeholder.com/300x300/eee/999?text=商品1', tag: '热卖' },
        { id: 2, name: '商品名称示例2', price: 19.90, originalPrice: 39.00, image: 'https://via.placeholder.com/300x300/eee/999?text=商品2', tag: '新品' },
        { id: 3, name: '商品名称示例3', price: 99.00, originalPrice: 199.00, image: 'https://via.placeholder.com/300x300/eee/999?text=商品3', tag: '特惠' },
        { id: 4, name: '商品名称示例4', price: 49.90, originalPrice: 89.00, image: 'https://via.placeholder.com/300x300/eee/999?text=商品4', tag: '' },
        { id: 5, name: '商品名称示例5', price: 39.00, originalPrice: 69.00, image: 'https://via.placeholder.com/300x300/eee/999?text=商品5', tag: '爆款' },
        { id: 6, name: '商品名称示例6', price: 15.90, originalPrice: 29.00, image: 'https://via.placeholder.com/300x300/eee/999?text=商品6', tag: '' }
      ]
    });
  },

  // 轮播图点击
  onBannerTap(e) {
    const { id } = e.currentTarget.dataset;
    console.log('banner tapped:', id);
  },

  // 分类点击
  onCategoryTap(e) {
    const { name } = e.currentTarget.dataset;
    wx.showToast({ title: name, icon: 'none' });
  },

  // 商品点击 → 跳转详情
  onProductTap(e) {
    const { id } = e.currentTarget.dataset;
    wx.navigateTo({ url: `/pages/goods/goods?id=${id}` });
  },

  // 搜索
  onSearchInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  onSearchConfirm() {
    wx.showToast({ title: `搜索: ${this.data.keyword}`, icon: 'none' });
  },

  // 购物车
  onCartTap() {
    wx.switchTab({ url: '/pages/cart/cart' });
  },

  // 下拉刷新
  onPullDownRefresh() {
    this.loadData();
    wx.stopPullDownRefresh();
  }
});
