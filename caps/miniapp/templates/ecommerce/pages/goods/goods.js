// pages/goods/goods.js — 商品详情
const app = getApp();

Page({
  data: {
    goods: null,
    currentImage: 0,
    qty: 1,
    showSpec: false
  },

  onLoad(options) {
    const id = parseInt(options.id) || 1;
    this.loadGoods(id);
  },

  loadGoods(id) {
    // 模拟商品数据 — 实际项目中从后端加载
    const goods = {
      id: id,
      name: '商品名称示例',
      price: 29.90,
      originalPrice: 59.00,
      sales: 1234,
      stock: 999,
      images: [
        'https://via.placeholder.com/750x750/eee/999?text=商品图1',
        'https://via.placeholder.com/750x750/ddd/999?text=商品图2',
        'https://via.placeholder.com/750x750/ccc/999?text=商品图3'
      ],
      specs: ['S', 'M', 'L', 'XL'],
      desc: `<p>这是商品的详细描述信息。</p><p>在这里可以展示商品的特点、材质、使用方法等。</p><p><img src="https://via.placeholder.com/700x400/eee/999?text=详情图" /></p>`
    };
    this.setData({ goods });
  },

  onSwiperChange(e) {
    this.setData({ currentImage: e.detail.current });
  },

  onImageTap() {
    const { goods, currentImage } = this.data;
    wx.previewImage({
      urls: goods.images,
      current: goods.images[currentImage]
    });
  },

  onQtyMinus() {
    if (this.data.qty > 1) {
      this.setData({ qty: this.data.qty - 1 });
    }
  },

  onQtyPlus() {
    if (this.data.qty < this.data.goods.stock) {
      this.setData({ qty: this.data.qty + 1 });
    }
  },

  onAddCart() {
    const { goods, qty } = this.data;
    const cart = app.globalData.cartItems;
    const idx = cart.findIndex(item => item.id === goods.id);
    if (idx >= 0) {
      cart[idx].qty += qty;
    } else {
      cart.push({
        id: goods.id,
        name: goods.name,
        price: goods.price,
        image: goods.images[0],
        qty
      });
    }
    app.saveCart();
    wx.showToast({ title: '已加入购物车', icon: 'success' });
  },

  onBuyNow() {
    this.onAddCart();
    wx.switchTab({ url: '/pages/cart/cart' });
  },

  onShareAppMessage() {
    const { goods } = this.data;
    return {
      title: goods.name,
      path: `/pages/goods/goods?id=${goods.id}`
    };
  }
});
