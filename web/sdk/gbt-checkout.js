/*!
 * GBT Checkout SDK v1.0.0
 * Self-contained embedded checkout widget for gbtxiaotudou.com
 * Inspired by Whop.com checkout architecture
 * License: MIT
 */
(function(root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.GBTCheckout = factory();
  }
}(typeof self !== 'undefined' ? self : this, function() {
  'use strict';

  // ═══════════════════════════════════════════════════════════════════════
  // QR Code Generator (minimal, embedded, canvas-based)
  // ═══════════════════════════════════════════════════════════════════════

  var QR = (function() {
    // GF(256) logarithm / exponent tables
    var expTable = new Uint8Array(512);
    var logTable = new Uint8Array(256);
    (function initGF() {
      var x = 1;
      for (var i = 0; i < 255; i++) {
        expTable[i] = x;
        logTable[x] = i;
        x = (x << 1) ^ (x & 0x80 ? 0x11D : 0);
      }
      for (var j = 255; j < 512; j++) {
        expTable[j] = expTable[j - 255];
      }
    })();

    function gfMul(a, b) {
      if (a === 0 || b === 0) return 0;
      return expTable[(logTable[a] + logTable[b]) % 255];
    }

    // Generator polynomial coefficients for EC codeword counts 7–68 (EC level M, versions 1–10)
    function buildGenPoly(ecCount) {
      var poly = [1];
      for (var i = 0; i < ecCount; i++) {
        var term = [0, 1];
        var next = new Array(poly.length + 1).fill(0);
        for (var j = 0; j < poly.length; j++) {
          next[j] ^= poly[j];
        }
        for (var k = 0; k < poly.length; k++) {
          next[k + 1] ^= gfMul(poly[k], expTable[i]);
        }
        poly = next;
      }
      while (poly.length > 1 && poly[poly.length - 1] === 0) poly.pop();
      return poly;
    }

    function rsEncode(data, ecCount) {
      var genPoly = buildGenPoly(ecCount);
      var msg = new Uint8Array(data.length + ecCount);
      msg.set(data, 0);

      for (var i = 0; i < data.length; i++) {
        var factor = msg[i];
        if (factor !== 0) {
          for (var j = 1; j < genPoly.length; j++) {
            msg[i + j] ^= gfMul(genPoly[j], factor);
          }
        }
      }
      return msg.slice(data.length);
    }

    // Version capacity table: [total codewords, EC codewords per block, blocks in group 1, codewords per block group 1, blocks in group 2, codewords per block group 2]
    // EC level M only, versions 1–10
    var VERSION_INFO = [
      null,
      [26, 10, 1, 16, 0, 0],   // v1
      [44, 16, 1, 28, 0, 0],   // v2
      [70, 26, 1, 44, 0, 0],   // v3
      [100, 18, 2, 32, 0, 0],  // v4
      [134, 24, 2, 43, 0, 0],  // v5
      [172, 16, 4, 27, 0, 0],  // v6
      [196, 18, 4, 31, 0, 0],  // v7
      [242, 22, 2, 34, 4, 33], // v8
      [292, 22, 3, 37, 3, 36], // v9
      [346, 26, 4, 40, 4, 39]  // v10
    ];

    // Alignment pattern positions per version
    var ALIGN_POS = {
      1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30],
      6: [6, 34], 7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 54]
    };

    function pickVersion(dataLen) {
      for (var v = 1; v <= 10; v++) {
        var info = VERSION_INFO[v];
        var totalData = info[2] * info[3] + info[4] * info[5];
        if (dataLen <= totalData) return v;
      }
      return 10; // max out at v10
    }

    function interleave(data, ecBlocks, version) {
      var info = VERSION_INFO[version];
      var ecCount = info[1];
      var g1Blocks = info[2], g1DataLen = info[3];
      var g2Blocks = info[4], g2DataLen = info[5];

      // Split data into blocks
      var blocks = [];
      var offset = 0;
      for (var i = 0; i < g1Blocks; i++) {
        blocks.push({ data: data.slice(offset, offset + g1DataLen), ec: null });
        offset += g1DataLen;
      }
      for (var j = 0; j < g2Blocks; j++) {
        blocks.push({ data: data.slice(offset, offset + g2DataLen), ec: null });
        offset += g2DataLen;
      }

      // Compute error correction for each block
      for (var k = 0; k < blocks.length; k++) {
        blocks[k].ec = rsEncode(blocks[k].data, ecCount);
      }

      // Interleave
      var result = [];
      var maxDataLen = Math.max(g1DataLen, g2DataLen);
      for (var di = 0; di < maxDataLen; di++) {
        for (var bi = 0; bi < blocks.length; bi++) {
          if (di < blocks[bi].data.length) result.push(blocks[bi].data[di]);
        }
      }
      for (var ei = 0; ei < ecCount; ei++) {
        for (var bj = 0; bj < blocks.length; bj++) {
          result.push(blocks[bj].ec[ei]);
        }
      }
      return result;
    }

    // Format info bits (EC level M, mask 0–7)
    var FORMAT_INFO = [
      0x5412, 0x5125, 0x5E7C, 0x5B4B, 0x45F9, 0x40CE, 0x4F97, 0x4AA0
    ];

    function makeMatrix(version) {
      var size = 17 + version * 4;
      var m = new Array(size);
      for (var i = 0; i < size; i++) m[i] = new Array(size).fill(-1);

      // Finder patterns (top-left, top-right, bottom-left)
      function placeFinder(r, c) {
        for (var i = 0; i < 7; i++) {
          for (var j = 0; j < 7; j++) {
            if (i <= 1 || i >= 5 || j <= 1 || j >= 5) {
              m[r + i][c + j] = 0;
            } else {
              m[r + i][c + j] = (i === 2 || i === 4 || j === 2 || j === 4) ? 1 : 0;
            }
          }
        }
      }
      placeFinder(0, 0);
      placeFinder(0, size - 7);
      placeFinder(size - 7, 0);

      // Timing patterns
      for (var i = 8; i < size - 8; i++) {
        m[6][i] = m[i][6] = (i % 2 === 0) ? 1 : 0;
      }

      // Alignment patterns
      var pos = ALIGN_POS[version];
      for (var ai = 0; ai < pos.length; ai++) {
        for (var aj = 0; aj < pos.length; aj++) {
          var r = pos[ai], c = pos[aj];
          // Skip if overlaps a finder pattern
          if ((r < 7 && c < 7) || (r < 7 && c > size - 8) || (r > size - 8 && c < 7)) continue;
          for (var di = -2; di <= 2; di++) {
            for (var dj = -2; dj <= 2; dj++) {
              m[r + di][c + dj] = (Math.abs(di) === 2 || Math.abs(dj) === 2 || (di === 0 && dj === 0)) ? 1 : 0;
            }
          }
        }
      }

      // Dark module
      m[size - 8][8] = 1;

      // Reserve format info areas (set to -2 for later fill)
      for (var fi = 0; fi < 8; fi++) m[8][fi] = -2;
      for (var fj = size - 8; fj < size; fj++) m[8][fj] = -2;
      for (var fk = 0; fk < 8; fk++) m[fk][8] = -2;
      for (var fl = size - 7; fl < size; fl++) m[fl][8] = -2;

      // Reserve version info areas (v7+)
      if (version >= 7) {
        for (var vi = 0; vi < 6; vi++) {
          for (var vj = size - 11; vj < size - 8; vj++) {
            m[vi][vj] = -3;
            m[vj][vi] = -3;
          }
        }
      }

      return m;
    }

    function applyMask(matrix, maskId) {
      var size = matrix.length;
      var masked = matrix.map(function(row) { return row.slice(); });

      for (var r = 0; r < size; r++) {
        for (var c = 0; c < size; c++) {
          if (masked[r][c] < 0) continue; // reserved
          var invert;
          switch (maskId) {
            case 0: invert = (r + c) % 2 === 0; break;
            case 1: invert = r % 2 === 0; break;
            case 2: invert = c % 3 === 0; break;
            case 3: invert = (r + c) % 3 === 0; break;
            case 4: invert = (Math.floor(r / 2) + Math.floor(c / 3)) % 2 === 0; break;
            case 5: invert = ((r * c) % 2) + ((r * c) % 3) === 0; break;
            case 6: invert = (((r * c) % 2) + ((r * c) % 3)) % 2 === 0; break;
            case 7: invert = (((r + c) % 2) + ((r * c) % 3)) % 2 === 0; break;
          }
          if (invert) masked[r][c] ^= 1;
        }
      }

      // Fill format info
      var fi = FORMAT_INFO[maskId];
      var size_ = size;
      var coords = [
        [0, 1, 2, 3, 4, 5, 7, 8, 8, 8, 8, 8, 8, 8, 8],
        [8, 8, 8, 8, 8, 8, 8, 8, 7, 5, 4, 3, 2, 1, 0]
      ];
      // Top-left format info
      for (var k = 0; k < 15; k++) {
        var bit = (fi >> k) & 1;
        masked[coords[0][k]][coords[1][k]] = bit;
        if (coords[1][k] !== 8) masked[coords[1][k]][coords[0][k]] = bit;
      }
      // Top-right / bottom-left format info copies
      for (var fi2 = 0; fi2 < 8; fi2++) {
        var b2 = (fi >> fi2) & 1;
        masked[8][size_ - 1 - fi2] = b2;
        masked[size_ - 1 - fi2][8] = b2;
      }

      for (var ri = 0; ri < size_; ri++) {
        for (var ci = 0; ci < size_; ci++) {
          if (masked[ri][ci] < 0) masked[ri][ci] = 0;
        }
      }

      return masked;
    }

    function score(matrix) {
      var size = matrix.length;
      var s = 0;

      // Adjacent modules in rows
      for (var r = 0; r < size; r++) {
        var runLen = 1, runVal = matrix[r][0];
        for (var c = 1; c < size; c++) {
          if (matrix[r][c] === runVal) {
            runLen++;
          } else {
            if (runLen >= 5) s += runLen - 2;
            runLen = 1;
            runVal = matrix[r][c];
          }
        }
        if (runLen >= 5) s += runLen - 2;
      }

      // Adjacent modules in columns
      for (var c = 0; c < size; c++) {
        var runLen2 = 1, runVal2 = matrix[0][c];
        for (var r = 1; r < size; r++) {
          if (matrix[r][c] === runVal2) {
            runLen2++;
          } else {
            if (runLen2 >= 5) s += runLen2 - 2;
            runLen2 = 1;
            runVal2 = matrix[r][c];
          }
        }
        if (runLen2 >= 5) s += runLen2 - 2;
      }

      // 2x2 blocks
      for (var r = 0; r < size - 1; r++) {
        for (var c = 0; c < size - 1; c++) {
          if (matrix[r][c] === matrix[r + 1][c] &&
              matrix[r][c] === matrix[r][c + 1] &&
              matrix[r][c] === matrix[r + 1][c + 1]) {
            s += 3;
          }
        }
      }

      // Finder-pattern-like
      for (var r = 0; r < size; r++) {
        for (var c = 0; c < size - 6; c++) {
          if (matrix[r][c] === 1 && matrix[r][c + 1] === 0 &&
              matrix[r][c + 2] === 1 && matrix[r][c + 3] === 1 &&
              matrix[r][c + 4] === 1 && matrix[r][c + 5] === 0 &&
              matrix[r][c + 6] === 1) s += 40;
        }
      }
      for (var r = 0; r < size - 6; r++) {
        for (var c = 0; c < size; c++) {
          if (matrix[r][c] === 1 && matrix[r + 1][c] === 0 &&
              matrix[r + 2][c] === 1 && matrix[r + 3][c] === 1 &&
              matrix[r + 4][c] === 1 && matrix[r + 5][c] === 0 &&
              matrix[r + 6][c] === 1) s += 40;
        }
      }

      // Balance
      var dark = 0;
      for (var r = 0; r < size; r++) {
        for (var c = 0; c < size; c++) {
          if (matrix[r][c]) dark++;
        }
      }
      var pct = dark / (size * size) * 100;
      s += Math.abs(pct - 50) * 2;

      return s;
    }

    function encode(dataStr) {
      // Convert to byte array
      var data = [];
      for (var i = 0; i < dataStr.length; i++) {
        var code = dataStr.charCodeAt(i);
        if (code < 0x80) {
          data.push(code);
        } else if (code < 0x800) {
          data.push(0xC0 | (code >> 6), 0x80 | (code & 0x3F));
        } else {
          data.push(0xE0 | (code >> 12), 0x80 | ((code >> 6) & 0x3F), 0x80 | (code & 0x3F));
        }
      }

      // Mode indicator: byte = 0100
      var version = pickVersion(data.length + 1); // +1 for mode+len overhead
      var info = VERSION_INFO[version];
      var totalData = info[2] * info[3] + info[4] * info[5];

      // Build bit stream
      var bits = [];
      function pushBits(val, len) {
        for (var i = len - 1; i >= 0; i--) bits.push((val >> i) & 1);
      }

      pushBits(4, 4); // byte mode

      // Character count indicator length depends on version
      var ccLen = version <= 9 ? 8 : 16;
      pushBits(data.length, ccLen);

      for (var i = 0; i < data.length; i++) {
        pushBits(data[i], 8);
      }

      // Terminator
      pushBits(0, Math.min(4, (totalData * 8) - bits.length));

      // Pad to byte boundary
      while (bits.length % 8 !== 0) bits.push(0);

      // Pad bytes
      var padBytes = [0xEC, 0x11];
      var pi = 0;
      while (bits.length < totalData * 8) {
        pushBits(padBytes[pi], 8);
        pi ^= 1;
      }

      // Convert to bytes
      var codewords = [];
      for (var i = 0; i < bits.length; i += 8) {
        var b = 0;
        for (var j = 0; j < 8; j++) b = (b << 1) | bits[i + j];
        codewords.push(b);
      }

      // Interleave + error correction
      var full = interleave(codewords, info[1], version);

      // Build matrix
      var matrix = makeMatrix(version);
      var size = matrix.length;

      // Place data modules (zig-zag pattern)
      var up = true;
      var col = size - 1;
      var row = size - 1;
      var di = 0;

      function isModuleFree(r, c) {
        return r >= 0 && r < size && c >= 0 && c < size && matrix[r][c] < 0;
      }

      while (col > 0) {
        if (col === 6) col = 5; // skip vertical timing pattern

        for (var sub = 0; sub < 2; sub++) {
          var c = col - (sub ^ 1);
          for (var r = up ? size - 1 : 0; up ? r >= 0 : r < size; r += up ? -1 : 1) {
            if (isModuleFree(r, c)) {
              matrix[r][c] = di < full.length * 8 ? ((full[di >> 3] >> (7 - (di & 7))) & 1) : 0;
              di++;
            }
          }
          up = !up;
        }
        col -= 2;
      }

      // Try all masks, pick best
      var bestMatrix = null, bestScore = Infinity;
      for (var m = 0; m < 8; m++) {
        var masked = applyMask(matrix, m);
        var s = score(masked);
        if (s < bestScore) {
          bestScore = s;
          bestMatrix = masked;
        }
      }

      return { matrix: bestMatrix, size: size };
    }

    function render(qr, canvas, moduleSize, fg, bg) {
      var ctx = canvas.getContext('2d');
      var size = qr.size * moduleSize;
      var dpr = window.devicePixelRatio || 1;
      canvas.width = size * dpr;
      canvas.height = size * dpr;
      canvas.style.width = size + 'px';
      canvas.style.height = size + 'px';
      ctx.scale(dpr, dpr);

      // Background
      ctx.fillStyle = bg || '#ffffff';
      ctx.fillRect(0, 0, size, size);

      // Modules
      ctx.fillStyle = fg || '#000000';
      var quiet = moduleSize; // 1-module quiet zone
      for (var r = 0; r < qr.size; r++) {
        for (var c = 0; c < qr.size; c++) {
          if (qr.matrix[r][c]) {
            ctx.fillRect(
              quiet + c * moduleSize,
              quiet + r * moduleSize,
              moduleSize,
              moduleSize
            );
          }
        }
      }
    }

    return {
      generate: function(dataStr, canvas) {
        var qr = encode(dataStr);
        var moduleSize = Math.max(3, Math.floor(200 / (qr.size + 2)));
        render(qr, canvas, moduleSize, '#000000', '#ffffff');
      }
    };
  })();

  // ═══════════════════════════════════════════════════════════════════════
  // Locale detection
  // ═══════════════════════════════════════════════════════════════════════

  var LOCALES = {
    en: {
      title: 'Complete Your Purchase',
      cardTab: 'Card',
      cryptoTab: 'Crypto',
      cardNumber: 'Card Number',
      expiry: 'MM / YY',
      cvc: 'CVC',
      pay: 'Pay',
      processing: 'Processing…',
      successTitle: 'Payment Successful!',
      successMessage: 'You will be redirected shortly.',
      errorTitle: 'Payment Failed',
      errorDefault: 'Something went wrong. Please try again.',
      validating: 'Please check your card details.',
      amount: 'Amount',
      method: 'Payment Method',
      selectMethod: 'Select payment method',
      usdt: 'USDT (TRC-20)',
      usdc: 'USDC (ERC-20)',
      usd: 'USD',
      payWith: 'Pay with',
      scanQR: 'Scan QR code to pay',
      copyAddress: 'Copy Address',
      copied: 'Copied!',
      cardLabel: 'Credit or Debit Card',
      cryptoLabel: 'Cryptocurrency',
      network: 'Network',
      trc20: 'TRON (TRC-20)',
      erc20: 'Ethereum (ERC-20)',
      polygon: 'Polygon'
    },
    zh: {
      title: '完成购买',
      cardTab: '银行卡',
      cryptoTab: '加密货币',
      cardNumber: '卡号',
      expiry: '月 / 年',
      cvc: '安全码',
      pay: '支付',
      processing: '处理中…',
      successTitle: '支付成功！',
      successMessage: '即将为您跳转。',
      errorTitle: '支付失败',
      errorDefault: '出现错误，请重试。',
      validating: '请检查您的卡信息。',
      amount: '金额',
      method: '支付方式',
      selectMethod: '选择支付方式',
      usdt: 'USDT (TRC-20)',
      usdc: 'USDC (ERC-20)',
      usd: 'USD',
      payWith: '支付方式',
      scanQR: '扫描二维码支付',
      copyAddress: '复制地址',
      copied: '已复制！',
      cardLabel: '信用卡/借记卡',
      cryptoLabel: '加密货币',
      network: '网络',
      trc20: 'TRON (TRC-20)',
      erc20: 'Ethereum (ERC-20)',
      polygon: 'Polygon'
    },
    ja: {
      title: '購入手続き',
      cardTab: 'カード',
      cryptoTab: '暗号通貨',
      cardNumber: 'カード番号',
      expiry: '月 / 年',
      cvc: 'セキュリティコード',
      pay: '支払う',
      processing: '処理中…',
      successTitle: '支払い完了！',
      successMessage: 'まもなくリダイレクトされます。',
      errorTitle: '支払い失敗',
      errorDefault: 'エラーが発生しました。もう一度お試しください。',
      validating: 'カード情報を確認してください。',
      amount: '金額',
      method: 'お支払い方法',
      selectMethod: 'お支払い方法を選択',
      usdt: 'USDT (TRC-20)',
      usdc: 'USDC (ERC-20)',
      usd: 'USD',
      payWith: '支払い方法',
      scanQR: 'QRコードをスキャン',
      copyAddress: 'アドレスをコピー',
      copied: 'コピーしました！',
      cardLabel: 'クレジット/デビットカード',
      cryptoLabel: '暗号通貨',
      network: 'ネットワーク',
      trc20: 'TRON (TRC-20)',
      erc20: 'Ethereum (ERC-20)',
      polygon: 'Polygon'
    },
    ko: {
      title: '결제하기',
      cardTab: '카드',
      cryptoTab: '암호화폐',
      cardNumber: '카드 번호',
      expiry: '월 / 연도',
      cvc: 'CVC',
      pay: '결제',
      processing: '처리 중…',
      successTitle: '결제 완료!',
      successMessage: '곧 리디렉션됩니다.',
      errorTitle: '결제 실패',
      errorDefault: '오류가 발생했습니다. 다시 시도해 주세요.',
      validating: '카드 정보를 확인해 주세요.',
      amount: '금액',
      method: '결제 방법',
      selectMethod: '결제 방법 선택',
      usdt: 'USDT (TRC-20)',
      usdc: 'USDC (ERC-20)',
      usd: 'USD',
      payWith: '결제 수단',
      scanQR: 'QR 코드 스캔',
      copyAddress: '주소 복사',
      copied: '복사됨!',
      cardLabel: '신용/직불 카드',
      cryptoLabel: '암호화폐',
      network: '네트워크',
      trc20: 'TRON (TRC-20)',
      erc20: 'Ethereum (ERC-20)',
      polygon: 'Polygon'
    }
  };

  function detectLocale() {
    var lang = (navigator.language || navigator.userLanguage || 'en').split('-')[0];
    return LOCALES[lang] || LOCALES.en;
  }

  function mergeLocale(custom) {
    if (!custom) return detectLocale();
    var base = detectLocale();
    var merged = {};
    for (var k in base) merged[k] = base[k];
    for (var k in custom) merged[k] = custom[k];
    return merged;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Card validation utilities
  // ═══════════════════════════════════════════════════════════════════════

  function luhnCheck(num) {
    var digits = num.replace(/\D/g, '');
    if (!digits) return false;
    var sum = 0;
    var alt = false;
    for (var i = digits.length - 1; i >= 0; i--) {
      var d = parseInt(digits[i], 10);
      if (alt) {
        d *= 2;
        if (d > 9) d -= 9;
      }
      sum += d;
      alt = !alt;
    }
    return sum % 10 === 0;
  }

  function detectCardBrand(num) {
    var n = num.replace(/\D/g, '');
    if (/^4/.test(n)) return { brand: 'visa', cvcLen: 3, maxLen: 16, mask: '0000 0000 0000 0000' };
    if (/^5[1-5]/.test(n)) return { brand: 'mastercard', cvcLen: 3, maxLen: 16, mask: '0000 0000 0000 0000' };
    if (/^3[47]/.test(n)) return { brand: 'amex', cvcLen: 4, maxLen: 15, mask: '0000 000000 00000' };
    if (/^6011|^65|^64[4-9]/.test(n)) return { brand: 'discover', cvcLen: 3, maxLen: 16, mask: '0000 0000 0000 0000' };
    if (/^35(2[89]|[3-8]\d)/.test(n)) return { brand: 'jcb', cvcLen: 3, maxLen: 16, mask: '0000 0000 0000 0000' };
    if (/^62/.test(n)) return { brand: 'unionpay', cvcLen: 3, maxLen: 19, mask: '0000 0000 0000 0000 000' };
    return { brand: 'generic', cvcLen: 3, maxLen: 16, mask: '0000 0000 0000 0000' };
  }

  function formatCardNumber(val) {
    var digits = val.replace(/\D/g, '');
    var brand = detectCardBrand(digits);
    var truncated = digits.slice(0, brand.maxLen);
    var groups = [];
    for (var i = 0; i < truncated.length; i += 4) {
      groups.push(truncated.slice(i, i + 4));
    }
    return groups.join(' ');
  }

  function formatExpiry(val) {
    var digits = val.replace(/\D/g, '');
    if (digits.length >= 2) {
      return digits.slice(0, 2) + ' / ' + digits.slice(2, 4);
    }
    return digits;
  }

  function validateExpiry(val) {
    var digits = val.replace(/\D/g, '');
    if (digits.length !== 4) return false;
    var month = parseInt(digits.slice(0, 2), 10);
    var year = parseInt(digits.slice(2, 4), 10) + 2000;
    if (month < 1 || month > 12) return false;
    var now = new Date();
    var expiry = new Date(year, month, 0); // last day of that month
    return expiry >= new Date(now.getFullYear(), now.getMonth(), 1);
  }

  // ═══════════════════════════════════════════════════════════════════════
  // GBTCheckoutEmbed class
  // ═══════════════════════════════════════════════════════════════════════

  /**
   * @param {Object} options
   * @param {string} options.planId      - plan identifier
   * @param {number} [options.amount]    - payment amount
   * @param {string} [options.planName]  - display name for the plan
   * @param {string} [options.coin]      - default coin: USDT, USDC, USD
   * @param {string} [options.theme]     - 'dark' (default) or 'light'
   * @param {string} [options.accentColor] - hex accent color (default: #ff6b35)
   * @param {string} [options.returnUrl] - URL to redirect after success
   * @param {string} [options.apiBase]   - API base URL (default: auto-detected)
   * @param {string} [options.locale]    - 'en', 'zh', 'ja', 'ko', or custom object
   * @param {Function} [options.onComplete] - callback(payload) on success
   * @param {Function} [options.onError]    - callback(error) on failure
   */
  function GBTCheckoutEmbed(options) {
    options = options || {};
    this.planId = options.planId || '';
    this.amount = options.amount || null;
    this.planName = options.planName || '';
    this.defaultCoin = (options.coin || 'USDT').toUpperCase();
    this.theme = options.theme === 'light' ? 'light' : 'dark';
    this.accentColor = options.accentColor || '#ff6b35';
    this.returnUrl = options.returnUrl || '';
    this.apiBase = options.apiBase || (function() {
      try { return location.origin; } catch(e) { return 'https://gbtxiaotudou.com'; }
    })();
    this.locale = mergeLocale(options.locale);
    this.onComplete = options.onComplete || null;
    this.onError = options.onError || null;

    this._state = 'idle'; // idle | loading | success | error
    this._method = 'card'; // card | crypto
    this._coin = this.defaultCoin;
    this._el = null;
    this._cardMeta = { brand: 'generic', cvcLen: 3, maxLen: 16 };
    this._pollInterval = null;
  }

  GBTCheckoutEmbed.prototype._t = function(key) {
    return this.locale[key] || key;
  };

  GBTCheckoutEmbed.prototype._elId = function(name) {
    return 'gbt-co-' + name;
  };

  GBTCheckoutEmbed.prototype.mount = function(container) {
    if (typeof container === 'string') {
      container = document.querySelector(container);
    }
    if (!container) throw new Error('GBT Checkout: container element not found');
    this._el = container;
    this._render();
    this._attach();
    return this;
  };

  GBTCheckoutEmbed.prototype._render = function() {
    var t = this._t.bind(this);
    var el = this._el;
    var accent = this.accentColor;
    var isDark = this.theme === 'dark';
    var bg = isDark ? '#0a0a0f' : '#ffffff';
    var bg2 = isDark ? '#12121a' : '#f5f5f7';
    var fg = isDark ? '#f5f5f7' : '#1d1d1f';
    var dim = isDark ? '#86868b' : '#6e6e73';
    var border = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)';
    var inputBg = isDark ? '#1a1a24' : '#ffffff';
    var inputBorder = isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.15)';
    var errColor = '#ff4757';
    var succColor = '#30d158';

    el.innerHTML = ''
      + '<div class="gbt-checkout-root" style="'
      + 'font-family:Inter,-apple-system,BlinkMacSystemFont,\'Segoe UI\',system-ui,sans-serif;'
      + 'color:' + fg + ';background:' + bg + ';'
      + 'border:1px solid ' + border + ';border-radius:16px;'
      + 'max-width:420px;margin:0 auto;overflow:hidden;'
      + 'font-size:14px;line-height:1.6;'
      + '-webkit-font-smoothing:antialiased;'
      + '">'

      // Header
      + '<div class="gbt-co-header" style="padding:24px 24px 0;">'
      + '<h3 style="margin:0 0 4px;font-size:20px;font-weight:700;color:' + fg + ';">' + t('title') + '</h3>'
      + (this.planName ? '<p style="margin:0;font-size:13px;color:' + dim + ';">' + escapeHTML(this.planName) + '</p>' : '')
      + '</div>'

      // Amount display
      + (this.amount ? ''
        + '<div style="margin:20px 24px 0;padding:16px;'
        + 'background:' + bg2 + ';border-radius:12px;'
        + 'border:1px solid ' + border + ';">'
        + '<div style="font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:' + dim + ';margin-bottom:4px;">' + t('amount') + '</div>'
        + '<div style="font-size:28px;font-weight:800;color:' + accent + ';letter-spacing:-0.02em;">$' + this.amount.toFixed(2) + '</div>'
        + '</div>'
      : '')

      // Method tabs
      + '<div style="display:flex;gap:4px;margin:20px 24px 0;padding:4px;'
      + 'background:' + bg2 + ';border-radius:10px;">'
      + '<button class="gbt-co-tab gbt-co-tab-card" data-method="card" style="'
      + 'flex:1;border:none;background:' + (this._method === 'card' ? accent : 'transparent') + ';'
      + 'color:' + (this._method === 'card' ? '#fff' : dim) + ';'
      + 'padding:10px 12px;border-radius:8px;font-size:13px;font-weight:600;'
      + 'cursor:pointer;transition:all 0.2s ease;font-family:inherit;'
      + '">' + t('cardTab') + '</button>'
      + '<button class="gbt-co-tab gbt-co-tab-crypto" data-method="crypto" style="'
      + 'flex:1;border:none;background:' + (this._method === 'crypto' ? accent : 'transparent') + ';'
      + 'color:' + (this._method === 'crypto' ? '#fff' : dim) + ';'
      + 'padding:10px 12px;border-radius:8px;font-size:13px;font-weight:600;'
      + 'cursor:pointer;transition:all 0.2s ease;font-family:inherit;'
      + '">' + t('cryptoTab') + '</button>'
      + '</div>'

      // Card form container
      + '<div class="gbt-co-card-form" style="display:' + (this._method === 'card' ? 'block' : 'none') + ';padding:20px 24px;">'
      + this._renderCardFormHTML(t, accent, fg, dim, errColor, inputBg, inputBorder)
      + '</div>'

      // Crypto form container
      + '<div class="gbt-co-crypto-form" style="display:' + (this._method === 'crypto' ? 'block' : 'none') + ';padding:20px 24px;">'
      + this._renderCryptoFormHTML(t, accent, fg, dim, inputBg, inputBorder, border)
      + '</div>'

      // Error message area
      + '<div class="gbt-co-error" style="display:none;margin:0 24px 16px;padding:12px 16px;'
      + 'background:rgba(255,71,87,0.1);border:1px solid rgba(255,71,87,0.25);'
      + 'border-radius:10px;color:' + errColor + ';font-size:13px;"></div>'

      // Submit button
      + '<div style="padding:0 24px 24px;">'
      + '<button class="gbt-co-submit" style="'
      + 'width:100%;padding:14px 24px;border:none;border-radius:12px;'
      + 'background:' + accent + ';color:#fff;font-size:15px;font-weight:700;'
      + 'cursor:pointer;transition:all 0.2s ease;font-family:inherit;'
      + 'letter-spacing:-0.01em;'
      + 'position:relative;overflow:hidden;'
      + '">'
      + '<span class="gbt-co-btn-text">' + t('pay') + '</span>'
      + '<span class="gbt-co-btn-spinner" style="display:none;position:absolute;inset:0;'
      + 'display:none;align-items:center;justify-content:center;background:' + accent + ';">'
      + '<svg width="20" height="20" viewBox="0 0 24 24" style="animation:gbt-spin 0.8s linear infinite;">'
      + '<circle cx="12" cy="12" r="10" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="3"/>'
      + '<path d="M12 2a10 10 0 0 1 10 10" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>'
      + '</svg></span>'
      + '</button>'
      + '</div>'

      // Loading overlay
      + '<div class="gbt-co-overlay" style="display:none;position:absolute;inset:0;'
      + 'background:' + (isDark ? 'rgba(0,0,0,0.7)' : 'rgba(255,255,255,0.85)') + ';'
      + 'z-index:10;align-items:center;justify-content:center;flex-direction:column;gap:16px;'
      + 'border-radius:16px;">'
      + '<div style="width:44px;height:44px;border:3px solid ' + border + ';'
      + 'border-top-color:' + accent + ';border-radius:50%;'
      + 'animation:gbt-spin 0.7s linear infinite;"></div>'
      + '<span style="font-size:14px;color:' + dim + ';font-weight:500;">' + t('processing') + '</span>'
      + '</div>'

      // Success overlay
      + '<div class="gbt-co-success" style="display:none;position:absolute;inset:0;'
      + 'background:' + bg + ';z-index:20;align-items:center;justify-content:center;'
      + 'flex-direction:column;gap:16px;border-radius:16px;text-align:center;padding:32px;">'
      + '<div style="width:64px;height:64px;border-radius:50%;background:' + succColor + ';'
      + 'display:flex;align-items:center;justify-content:center;">'
      + '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">'
      + '<polyline points="20 6 9 17 4 12"/>'
      + '</svg></div>'
      + '<div style="font-size:18px;font-weight:700;color:' + fg + ';">' + t('successTitle') + '</div>'
      + '<div style="font-size:14px;color:' + dim + ';">' + t('successMessage') + '</div>'
      + '</div>'

      + '<style>'
      + '@keyframes gbt-spin{to{transform:rotate(360deg)}}'
      + '@keyframes gbt-fade-in{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}'
      + '@keyframes gbt-shake{0%,100%{transform:translateX(0)}20%{transform:translateX(-6px)}40%{transform:translateX(6px)}60%{transform:translateX(-4px)}80%{transform:translateX(4px)}}'
      + '.gbt-co-input:focus{outline:none;border-color:' + accent + '!important;box-shadow:0 0 0 3px ' + hexToRgba(accent, 0.15) + ';}'
      + '.gbt-co-input.error{border-color:' + errColor + '!important;box-shadow:0 0 0 3px rgba(255,71,87,0.12);animation:gbt-shake 0.4s ease;}'
      + '.gbt-co-submit:hover{filter:brightness(1.15);}'
      + '.gbt-co-submit:active{transform:scale(0.98);}'
      + '.gbt-co-submit:disabled{opacity:0.5;cursor:not-allowed;filter:none;}'
      + '.gbt-co-copy:hover{background:rgba(255,255,255,0.1);}'
      + '.gbt-co-coin-btn.selected{border-color:' + accent + '!important;background:' + hexToRgba(accent, 0.1) + '!important;}'
      + '</style>'
      + '</div>';
  };

  GBTCheckoutEmbed.prototype._renderCardFormHTML = function(t, accent, fg, dim, errColor, inputBg, inputBorder) {
    return ''
      + '<div style="margin-bottom:16px;">'
      + '<label style="display:block;font-size:12px;font-weight:600;color:' + dim + ';'
      + 'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">' + t('cardNumber') + '</label>'
      + '<div style="position:relative;">'
      + '<input class="gbt-co-input gbt-co-card-number" type="text" inputmode="numeric" autocomplete="cc-number"'
      + ' placeholder="0000 0000 0000 0000" maxlength="24"'
      + ' style="width:100%;padding:12px 14px;border:1px solid ' + inputBorder + ';'
      + 'border-radius:10px;background:' + inputBg + ';color:' + fg + ';'
      + 'font-size:16px;font-family:\'SF Mono\',\'JetBrains Mono\',\'Consolas\',monospace;'
      + 'letter-spacing:0.04em;transition:all 0.2s ease;box-sizing:border-box;">'
      + '<span class="gbt-co-card-brand" style="position:absolute;right:14px;top:50%;transform:translateY(-50%);'
      + 'font-size:12px;font-weight:700;color:' + dim + ';pointer-events:none;text-transform:uppercase;"></span>'
      + '</div>'
      + '</div>'
      + '<div style="display:flex;gap:12px;margin-bottom:16px;">'
      + '<div style="flex:1;">'
      + '<label style="display:block;font-size:12px;font-weight:600;color:' + dim + ';'
      + 'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">' + t('expiry') + '</label>'
      + '<input class="gbt-co-input gbt-co-expiry" type="text" inputmode="numeric" autocomplete="cc-exp"'
      + ' placeholder="MM / YY" maxlength="7"'
      + ' style="width:100%;padding:12px 14px;border:1px solid ' + inputBorder + ';'
      + 'border-radius:10px;background:' + inputBg + ';color:' + fg + ';'
      + 'font-size:16px;font-family:\'SF Mono\',\'JetBrains Mono\',\'Consolas\',monospace;'
      + 'transition:all 0.2s ease;box-sizing:border-box;">'
      + '</div>'
      + '<div style="flex:1;">'
      + '<label style="display:block;font-size:12px;font-weight:600;color:' + dim + ';'
      + 'text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">' + t('cvc') + '</label>'
      + '<input class="gbt-co-input gbt-co-cvc" type="text" inputmode="numeric" autocomplete="cc-csc"'
      + ' placeholder="123" maxlength="4"'
      + ' style="width:100%;padding:12px 14px;border:1px solid ' + inputBorder + ';'
      + 'border-radius:10px;background:' + inputBg + ';color:' + fg + ';'
      + 'font-size:16px;font-family:\'SF Mono\',\'JetBrains Mono\',\'Consolas\',monospace;'
      + 'transition:all 0.2s ease;box-sizing:border-box;">'
      + '</div>'
      + '</div>'
      // Supported card icons
      + '<div style="display:flex;gap:8px;align-items:center;justify-content:center;margin-top:4px;">'
      + '<svg width="32" height="20" viewBox="0 0 32 20" style="opacity:0.4;"><rect width="32" height="20" rx="3" fill="#1A1F71"/><text x="16" y="14" text-anchor="middle" fill="white" font-size="9" font-weight="700" font-family="sans-serif">VISA</text></svg>'
      + '<svg width="32" height="20" viewBox="0 0 32 20" style="opacity:0.4;"><rect width="32" height="20" rx="3" fill="#252525"/><circle cx="14" cy="10" r="6" fill="#EB001B"/><circle cx="19" cy="10" r="6" fill="#F79E1B" opacity="0.8"/></svg>'
      + '<svg width="32" height="20" viewBox="0 0 32 20" style="opacity:0.4;"><rect width="32" height="20" rx="3" fill="#016FD0"/><text x="16" y="14" text-anchor="middle" fill="white" font-size="7" font-weight="700" font-family="sans-serif">AMEX</text></svg>'
      + '<svg width="32" height="20" viewBox="0 0 32 20" style="opacity:0.4;"><rect width="32" height="20" rx="3" fill="white" stroke="#ddd"/><circle cx="16" cy="10" r="6" fill="#FF5A00"/></svg>'
      + '</div>';
  };

  GBTCheckoutEmbed.prototype._renderCryptoFormHTML = function(t, accent, fg, dim, inputBg, inputBorder, border) {
    var coins = ['USDT', 'USDC', 'USD'];
    var isDark = this.theme === 'dark';

    var coinBtns = '';
    for (var i = 0; i < coins.length; i++) {
      var c = coins[i];
      var selected = this._coin === c;
      coinBtns += ''
        + '<button class="gbt-co-coin-btn' + (selected ? ' selected' : '') + '" data-coin="' + c + '" style="'
        + 'flex:1;border:1px solid ' + (selected ? accent : inputBorder) + ';'
        + 'background:' + (selected ? hexToRgba(accent, 0.1) : inputBg) + ';'
        + 'padding:10px 8px;border-radius:10px;color:' + (selected ? accent : dim) + ';'
        + 'font-size:13px;font-weight:600;cursor:pointer;transition:all 0.2s ease;font-family:inherit;'
        + '">' + t(c.toLowerCase()) + '</button>';
    }

    return ''
      + '<div style="display:flex;gap:6px;margin-bottom:20px;">' + coinBtns + '</div>'
      // QR code area
      + '<div class="gbt-co-qr-area" style="display:' + (this._state === 'crypto-pending' ? 'block' : 'none') + ';'
      + 'text-align:center;padding:20px;background:' + (isDark ? '#12121a' : '#f9f9fb') + ';'
      + 'border-radius:12px;border:1px solid ' + border + ';margin-bottom:16px;">'
      + '<div style="font-size:13px;font-weight:600;margin-bottom:12px;color:' + dim + ';">' + t('scanQR') + '</div>'
      + '<canvas class="gbt-co-qr-canvas" style="max-width:180px;border-radius:8px;"></canvas>'
      + '</div>'
      // Address display (hidden until payment created)
      + '<div class="gbt-co-address-display" style="display:none;margin-bottom:16px;">'
      + '<div style="font-size:12px;font-weight:600;color:' + dim + ';text-transform:uppercase;'
      + 'letter-spacing:0.05em;margin-bottom:6px;">' + t('payWith') + ' ' + t(this._coin.toLowerCase()) + '</div>'
      + '<div style="display:flex;gap:8px;">'
      + '<code class="gbt-co-address-text" style="flex:1;padding:10px 12px;background:' + inputBg + ';'
      + 'border:1px solid ' + inputBorder + ';border-radius:10px;font-size:12px;color:' + fg + ';'
      + 'word-break:break-all;font-family:\'SF Mono\',\'JetBrains Mono\',\'Consolas\',monospace;'
      + 'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;line-height:1.6;"></code>'
      + '<button class="gbt-co-copy" style="flex-shrink:0;padding:10px 14px;border:1px solid ' + inputBorder + ';'
      + 'border-radius:10px;background:' + inputBg + ';color:' + dim + ';font-size:12px;font-weight:600;'
      + 'cursor:pointer;transition:all 0.2s ease;font-family:inherit;white-space:nowrap;">'
      + t('copyAddress') + '</button>'
      + '</div>'
      + '<div class="gbt-co-copied-msg" style="display:none;margin-top:6px;font-size:12px;color:' + accent + ';font-weight:600;">'
      + t('copied') + '</div>'
      + '</div>'
      // Network badge
      + '<div style="padding:8px 16px;background:' + (isDark ? '#12121a' : '#f9f9fb') + ';'
      + 'border-radius:10px;font-size:12px;color:' + dim + ';text-align:center;margin-bottom:8px;">'
      + t('network') + ': <strong style="color:' + fg + ';">'
      + (this._coin === 'USDT' ? t('trc20') : this._coin === 'USDC' ? t('erc20') : t('polygon'))
      + '</strong></div>';
  };

  GBTCheckoutEmbed.prototype._attach = function() {
    var self = this;
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;

    // Method tab switching
    var tabs = root.querySelectorAll('.gbt-co-tab');
    for (var i = 0; i < tabs.length; i++) {
      tabs[i].addEventListener('click', function() {
        var method = this.dataset.method;
        self._switchMethod(method);
      });
    }

    // Coin selection (crypto)
    var coinBtns = root.querySelectorAll('.gbt-co-coin-btn');
    for (var j = 0; j < coinBtns.length; j++) {
      coinBtns[j].addEventListener('click', function() {
        var coin = this.dataset.coin;
        self._selectCoin(coin);
      });
    }

    // Card input formatting
    var cardInput = root.querySelector('.gbt-co-card-number');
    if (cardInput) {
      cardInput.addEventListener('input', function() {
        var raw = this.value;
        var formatted = formatCardNumber(raw);
        this.value = formatted;
        self._cardMeta = detectCardBrand(raw);
        // Update brand label
        var brandEl = root.querySelector('.gbt-co-card-brand');
        if (brandEl) {
          brandEl.textContent = self._cardMeta.brand === 'generic' ? '' : self._cardMeta.brand;
        }
        // Update CVC maxlength
        var cvcInput = root.querySelector('.gbt-co-cvc');
        if (cvcInput) {
          cvcInput.maxLength = self._cardMeta.cvcLen;
          cvcInput.placeholder = self._cardMeta.cvcLen === 4 ? '0000' : '000';
        }
        self._clearError();
      });
    }

    var expiryInput = root.querySelector('.gbt-co-expiry');
    if (expiryInput) {
      expiryInput.addEventListener('input', function() {
        this.value = formatExpiry(this.value);
        self._clearError();
      });
    }

    var cvcInput = root.querySelector('.gbt-co-cvc');
    if (cvcInput) {
      cvcInput.addEventListener('input', function() {
        this.value = this.value.replace(/\D/g, '');
        self._clearError();
      });
    }

    // Copy button
    var copyBtn = root.querySelector('.gbt-co-copy');
    if (copyBtn) {
      copyBtn.addEventListener('click', function() {
        var addrEl = root.querySelector('.gbt-co-address-text');
        if (!addrEl) return;
        var addr = addrEl.textContent;
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(addr).then(function() {
            self._showCopied();
          });
        } else {
          // Fallback
          var ta = document.createElement('textarea');
          ta.value = addr;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
          self._showCopied();
        }
      });
    }

    // Submit
    var submitBtn = root.querySelector('.gbt-co-submit');
    if (submitBtn) {
      submitBtn.addEventListener('click', function() {
        self._handleSubmit();
      });
    }
  };

  GBTCheckoutEmbed.prototype._switchMethod = function(method) {
    this._method = method;
    this._state = 'idle';
    this._clearError();
    this._render();
    this._attach();
  };

  GBTCheckoutEmbed.prototype._selectCoin = function(coin) {
    var valid = ['USDT', 'USDC', 'USD'];
    if (valid.indexOf(coin) === -1) return;
    this._coin = coin;
    this._state = 'idle';
    this._clearError();
    this._render();
    this._attach();
  };

  GBTCheckoutEmbed.prototype._showCopied = function() {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;
    var msg = root.querySelector('.gbt-co-copied-msg');
    if (msg) {
      msg.style.display = 'block';
      setTimeout(function() { msg.style.display = 'none'; }, 2000);
    }
  };

  GBTCheckoutEmbed.prototype._showError = function(msg) {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;
    var errEl = root.querySelector('.gbt-co-error');
    if (errEl) {
      errEl.textContent = msg;
      errEl.style.display = 'block';
      errEl.style.animation = 'gbt-shake 0.4s ease';
    }
  };

  GBTCheckoutEmbed.prototype._clearError = function() {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;
    var errEl = root.querySelector('.gbt-co-error');
    if (errEl) errEl.style.display = 'none';
  };

  GBTCheckoutEmbed.prototype._setLoading = function(loading) {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;
    var submitBtn = root.querySelector('.gbt-co-submit');
    var btnText = root.querySelector('.gbt-co-btn-text');
    var btnSpinner = root.querySelector('.gbt-co-btn-spinner');
    var overlay = root.querySelector('.gbt-co-overlay');

    if (submitBtn) submitBtn.disabled = loading;
    if (btnText) btnText.style.display = loading ? 'none' : '';
    if (btnSpinner) btnSpinner.style.display = loading ? 'flex' : 'none';
    if (overlay) overlay.style.display = loading ? 'flex' : 'none';

    this._state = loading ? 'loading' : 'idle';
  };


  GBTCheckoutEmbed.prototype._setStatus = function(msg) {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;
    var statusEl = root.querySelector('.gbt-co-status');
    if (!statusEl) {
      statusEl = document.createElement('div');
      statusEl.className = 'gbt-co-status';
      statusEl.style.cssText = 'text-align:center;padding:16px;color:#10b981;font-size:15px;font-weight:600;animation:gbt-pulse 1.5s infinite';
      var content = root.querySelector('.gbt-co-content') || root;
      content.appendChild(statusEl);
    }
    statusEl.textContent = msg;
    statusEl.style.display = 'block';
  };
  GBTCheckoutEmbed.prototype._showSuccess = function(payload) {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return;
    var successEl = root.querySelector('.gbt-co-success');
    if (successEl) {
      successEl.style.display = 'flex';
      successEl.style.animation = 'gbt-fade-in 0.4s ease';
    }
    // Hide form elements
    var cardForm = root.querySelector('.gbt-co-card-form');
    var cryptoForm = root.querySelector('.gbt-co-crypto-form');
    var submitArea = root.querySelector('.gbt-co-submit');
    var tabs = root.querySelectorAll('.gbt-co-tab');
    if (cardForm) cardForm.style.display = 'none';
    if (cryptoForm) cryptoForm.style.display = 'none';
    if (submitArea) submitArea.parentElement.style.display = 'none';
    for (var i = 0; i < tabs.length; i++) tabs[i].parentElement.style.display = 'none';
    // Hide header amount
    var header = root.querySelector('.gbt-co-header');
    // Actually hide everything except success
    var allChildren = root.children;
    for (var j = 0; j < allChildren.length; j++) {
      if (allChildren[j] !== successEl && allChildren[j].tagName !== 'STYLE') {
        allChildren[j].style.display = 'none';
      }
    }

    this._state = 'success';

    if (this.onComplete) {
      this.onComplete(payload);
    }

    if (this.returnUrl) {
      setTimeout(function() {
        window.location.href = this.returnUrl;
      }.bind(this), 2000);
    }
  };

  GBTCheckoutEmbed.prototype._validateCard = function() {
    var root = this._el.querySelector('.gbt-checkout-root');
    if (!root) return false;

    var cardNum = (root.querySelector('.gbt-co-card-number') || {}).value || '';
    var expiry = (root.querySelector('.gbt-co-expiry') || {}).value || '';
    var cvc = (root.querySelector('.gbt-co-cvc') || {}).value || '';

    var digits = cardNum.replace(/\D/g, '');
    var cvcDigits = cvc.replace(/\D/g, '');

    if (digits.length < 13) {
      this._showError(this._t('validating') + ' — ' + this._t('cardNumber'));
      var cn = root.querySelector('.gbt-co-card-number');
      if (cn) cn.classList.add('error');
      return false;
    }

    if (!luhnCheck(digits)) {
      this._showError(this._t('validating') + ' — ' + this._t('cardNumber'));
      var cn2 = root.querySelector('.gbt-co-card-number');
      if (cn2) cn2.classList.add('error');
      return false;
    }

    if (!validateExpiry(expiry)) {
      this._showError(this._t('validating') + ' — ' + this._t('expiry'));
      var ex = root.querySelector('.gbt-co-expiry');
      if (ex) ex.classList.add('error');
      return false;
    }

    if (cvcDigits.length < this._cardMeta.cvcLen) {
      this._showError(this._t('validating') + ' — ' + this._t('cvc'));
      var cvcEl = root.querySelector('.gbt-co-cvc');
      if (cvcEl) cvcEl.classList.add('error');
      return false;
    }

    return true;
  };

  GBTCheckoutEmbed.prototype._handleSubmit = function() {
    var self = this;

    if (this._method === 'card') {
      if (!this._validateCard()) return;
      this._processCardPayment();
    } else {
      this._processCryptoPayment();
    }
  };

  GBTCheckoutEmbed.prototype._processCardPayment = function() {
    var self = this;
    self._setLoading(true);

    var body = {
      coin: 'USD',
      amount: self.amount || 0,
      method: 'stripe',
      order_id: 'gbt-card-' + Date.now(),
      project: self.planId || 'checkout'
    };

    fetch(self.apiBase + '/api/payment/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (data.success) {
        self._showSuccess(data);
      } else {
        throw new Error(data.error || self._t('errorDefault'));
      }
    })
    .catch(function(err) {
      self._setLoading(false);
      self._showError(err.message || self._t('errorDefault'));
      if (self.onError) self.onError(err);
    });
  };

  GBTCheckoutEmbed.prototype._processCryptoPayment = function() {
    var self = this;
    self._setLoading(true);

    // Determine the backend method based on coin
    var methodMap = { USDT: 'cryptapi', USDC: 'cryptapi', USD: 'coinflow' };
    var method = methodMap[this._coin] || 'cryptapi';

    var body = {
      coin: self._coin,
      amount: self.amount || 0,
      method: method,
      order_id: 'gbt-crypto-' + Date.now(),
      project: self.planId || 'checkout'
    };

    fetch(self.apiBase + '/api/payment/create', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      if (!data.success) {
        throw new Error(data.error || self._t('errorDefault'));
      }

      self._state = 'crypto-pending';
      self._setLoading(false);
      self._render();
      self._attach();

      // Show address and QR
      var root = self._el.querySelector('.gbt-checkout-root');
      if (!root) return;

      // Display address
      var addrDisplay = root.querySelector('.gbt-co-address-display');
      var addrText = root.querySelector('.gbt-co-address-text');
      if (addrDisplay && addrText) {
        addrDisplay.style.display = 'block';
        addrText.textContent = data.payment_address || data.payment_url || '';
      }

      // Render QR code
      var qrArea = root.querySelector('.gbt-co-qr-area');
      var qrCanvas = root.querySelector('.gbt-co-qr-canvas');
      if (qrArea && qrCanvas) {
        qrArea.style.display = 'block';
        var qrData = data.payment_url || data.payment_address || '';
        if (qrData) {
          QR.generate(qrData, qrCanvas);
        }
      }

      // Start polling for payment status
      self._startPolling(data.order_id);
    })
    .catch(function(err) {
      self._setLoading(false);
      self._showError(err.message || self._t('errorDefault'));
      if (self.onError) self.onError(err);
    });
  };

  GBTCheckoutEmbed.prototype._startPolling = function(orderId) {
    var self = this;
    this._stopPolling();

    this._pollInterval = setInterval(function() {
      fetch(self.apiBase + '/api/payment/status/' + orderId)
        .then(function(r) { return r.json(); })
        .then(function(data) {
          if (data.status === 'completed' || data.status === 'confirmed' || data.status === 'paid' || data.status === 'settled') {
            self._stopPolling();
            self._showSuccess(data.status === 'settled' ? { ...data, status: 'settled', message: '已到账 ✅' } : data);
          } else if (data.status === 'settling') {
            self._setStatus('⏳ 链上确认中...');
          } else if (data.status === 'failed' || data.status === 'expired' || data.status === 'cancelled') {
            self._stopPolling();
            self._setLoading(false);
            self._showError(data.error || self._t('errorDefault'));
            if (self.onError) self.onError(new Error(data.error || self._t('errorDefault')));
          }
        })
        .catch(function() {
          // Silently ignore polling errors
        });
    }, 5000); // poll every 5 seconds
  };

  GBTCheckoutEmbed.prototype._stopPolling = function() {
    if (this._pollInterval) {
      clearInterval(this._pollInterval);
      this._pollInterval = null;
    }
  };

  GBTCheckoutEmbed.prototype.destroy = function() {
    this._stopPolling();
    if (this._el) {
      this._el.innerHTML = '';
    }
  };

  // ═══════════════════════════════════════════════════════════════════════
  // Helpers
  // ═══════════════════════════════════════════════════════════════════════

  function hexToRgba(hex, alpha) {
    hex = hex.replace('#', '');
    if (hex.length === 3) {
      hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    var r = parseInt(hex.substring(0, 2), 16);
    var g = parseInt(hex.substring(2, 4), 16);
    var b = parseInt(hex.substring(4, 6), 16);
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }

  function escapeHTML(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Static API
  // ═══════════════════════════════════════════════════════════════════════

  function mount(selector, options) {
    var el = typeof selector === 'string' ? document.querySelector(selector) : selector;
    if (!el) throw new Error('GBT Checkout: element not found: ' + selector);
    var instance = new GBTCheckoutEmbed(options);
    instance.mount(el);
    return instance;
  }

  function autoMount() {
    if (typeof document === 'undefined') return [];
    var elements = document.querySelectorAll('[data-gbt-checkout-plan-id]');
    var instances = [];
    for (var i = 0; i < elements.length; i++) {
      var el = elements[i];
      var options = {
        planId: el.dataset.gbtCheckoutPlanId,
        planName: el.dataset.gbtCheckoutPlanName || el.dataset.gbtPlanName || '',
        amount: el.dataset.gbtCheckoutAmount ? parseFloat(el.dataset.gbtCheckoutAmount) : (el.dataset.gbtAmount ? parseFloat(el.dataset.gbtAmount) : null),
        coin: el.dataset.gbtCheckoutCoin || el.dataset.gbtCoin || 'USDT',
        theme: el.dataset.gbtCheckoutTheme || el.dataset.gbtTheme || 'dark',
        accentColor: el.dataset.gbtCheckoutAccent || el.dataset.gbtAccent || '#ff6b35',
        returnUrl: el.dataset.gbtCheckoutReturnUrl || el.dataset.gbtReturnUrl || '',
        apiBase: el.dataset.gbtCheckoutApiBase || el.dataset.gbtApiBase || '',
        locale: el.dataset.gbtCheckoutLocale || el.dataset.gbtLocale || null,
        onComplete: null, // cannot be set via data attributes
        onError: null
      };
      var instance = new GBTCheckoutEmbed(options);
      instance.mount(el);
      instances.push(instance);
    }
    return instances;
  }

  // Auto-mount on DOM ready
  if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', autoMount);
    } else {
      autoMount();
    }
  }

  // ═══════════════════════════════════════════════════════════════════════
  // Exports
  // ═══════════════════════════════════════════════════════════════════════

  return {
    Checkout: GBTCheckoutEmbed,
    mount: mount,
    autoMount: autoMount,
    VERSION: '1.0.0'
  };

}));
