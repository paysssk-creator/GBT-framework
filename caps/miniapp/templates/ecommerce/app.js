// {{PROJECT_NAME}} — 微信小程序电商模板
App({
  onLaunch() {
    // 初始化全局数据
    this.globalData = {
      userInfo: null,
      cartCount: 0,
      cartItems: [],
      baseUrl: 'https://your-api-server.com'
    };

    // 从本地缓存恢复购物车
    const cart = wx.getStorageSync('cart');
    if (cart) {
      this.globalData.cartItems = cart;
      this.globalData.cartCount = cart.reduce((sum, item) => sum + item.qty, 0);
    }

    // 登录
    wx.login({
      success: () => {
        // 可将 code 发送至后端换取 openid / session_key
      }
    });
  },

  updateCartCount() {
    const cart = this.globalData.cartItems;
    this.globalData.cartCount = cart.reduce((sum, item) => sum + item.qty, 0);
  },

  saveCart() {
    wx.setStorageSync('cart', this.globalData.cartItems);
    this.updateCartCount();
  }
});
