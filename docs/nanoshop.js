/**
 * SolarPunk Nanoshop v1 — embeddable micro-storefront widget
 * ===========================================================
 * Drop this anywhere on the web. Replaces the ad unit concept.
 * User sees a clean mini-shop overlay, clicks once to buy via PayPal.me,
 * or hits × and it's gone. No tracking. No accounts. Just a purchase.
 *
 * EMBED OPTIONS:
 *
 * 1. Self-configuring (reads product from nanoshop-index.json):
 *    <script src="https://meekotharaccoon-cell.github.io/meeko-nerve-center/nanoshop.js"></script>
 *
 * 2. Specific product:
 *    <script src="...nanoshop.js"
 *      data-product-id="solarpunk-starter"
 *      data-title="Build Your Own SolarPunk"
 *      data-price="1.00"
 *      data-paypal="https://www.paypal.me/meekotharaccoon/1USD"
 *      data-gaza="15"
 *      data-delay="4000">
 *    </script>
 *
 * 3. JavaScript API:
 *    SolarPunkNanoshop.show({ title, price, paypal, gaza, delay })
 *    SolarPunkNanoshop.hide()
 *
 * Config via window.NANOSHOP_CONFIG = { ... } before script loads.
 */

(function() {
  'use strict';

  var BASE = 'https://meekotharaccoon-cell.github.io/meeko-nerve-center';
  var INDEX_URL = BASE + '/nanoshop-index.json';
  var DISMISS_KEY = 'sp_nanoshop_dismissed';
  var DISMISS_TTL = 4 * 60 * 60 * 1000; // 4 hours — reappears next visit

  // ─── Read config ────────────────────────────────────────────────────────────
  var scriptEl = document.currentScript || (function() {
    var scripts = document.querySelectorAll('script[src*="nanoshop"]');
    return scripts[scripts.length - 1];
  })();

  function attr(name, fallback) {
    return (scriptEl && scriptEl.getAttribute('data-' + name)) || fallback;
  }

  var userConfig = window.NANOSHOP_CONFIG || {};

  var config = {
    productId: attr('product-id', userConfig.productId || null),
    title:     attr('title',      userConfig.title     || null),
    price:     attr('price',      userConfig.price     || null),
    paypal:    attr('paypal',     userConfig.paypal    || null),
    gaza:      attr('gaza',       userConfig.gaza      || '15'),
    delay:     parseInt(attr('delay', userConfig.delay || '3500'), 10),
    position:  attr('position',   userConfig.position  || 'bottom-right'), // bottom-right | bottom-left | center
  };

  // ─── Dismiss state ───────────────────────────────────────────────────────────
  function isDismissed() {
    try {
      var v = localStorage.getItem(DISMISS_KEY);
      if (!v) return false;
      var data = JSON.parse(v);
      if (Date.now() - data.ts < DISMISS_TTL) return true;
      localStorage.removeItem(DISMISS_KEY);
      return false;
    } catch(e) { return false; }
  }

  function markDismissed() {
    try { localStorage.setItem(DISMISS_KEY, JSON.stringify({ ts: Date.now() })); }
    catch(e) {}
  }

  // ─── Gaza bar gradient ───────────────────────────────────────────────────────
  function gazaBar(pct) {
    pct = parseInt(pct, 10) || 15;
    var color = pct >= 70 ? '#e87c5a' : '#c8a86b';
    return '<div style="margin:10px 0 6px;background:rgba(255,255,255,.06);border-radius:4px;height:5px;overflow:hidden">' +
      '<div style="width:' + pct + '%;height:100%;background:' + color + '"></div></div>' +
      '<div style="font-size:9px;color:rgba(255,255,255,.4);letter-spacing:.04em">' +
        pct + '% OF PURCHASE → GAZA CHILDREN · PCRF EIN 93-1057665' +
      '</div>';
  }

  // ─── Build widget HTML ────────────────────────────────────────────────────────
  function buildWidget(product) {
    var posStyles = {
      'bottom-right': 'bottom:20px;right:20px',
      'bottom-left':  'bottom:20px;left:20px',
      'center': 'top:50%;left:50%;transform:translate(-50%,-50%)',
    };
    var pos = posStyles[config.position] || posStyles['bottom-right'];

    var title   = product.title   || 'SolarPunk Guide';
    var price   = product.price   || '1.00';
    var paypal  = product.paypal  || (BASE + '/shop.html');
    var gaza    = product.gaza    || config.gaza || '15';
    var gumroad = product.gumroad || '';

    var el = document.createElement('div');
    el.id = 'sp-nanoshop';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-label', 'SolarPunk — quick purchase');

    el.innerHTML = [
      '<div style="font-family:-apple-system,BlinkMacSystemFont,\'Segoe UI\',sans-serif;',
               'background:#0c0c1e;border:1px solid rgba(200,168,107,.25);',
               'border-radius:14px;padding:18px 20px 16px;width:280px;',
               'box-shadow:0 8px 40px rgba(0,0,0,.7);color:#e0e0e0;',
               'position:fixed;z-index:2147483647;' + pos + ';',
               'animation:sp-fadein .3s ease">',

        /* close */
        '<button id="sp-x" aria-label="Close" style="',
          'position:absolute;top:10px;right:12px;background:none;border:none;',
          'color:rgba(255,255,255,.35);font-size:18px;cursor:pointer;',
          'line-height:1;padding:0;transition:color .2s" ',
          'onmouseover="this.style.color=\'rgba(255,255,255,.8)\'" ',
          'onmouseout="this.style.color=\'rgba(255,255,255,.35)\'">×</button>',

        /* brand */
        '<div style="font-size:9px;color:rgba(200,168,107,.6);letter-spacing:.08em;margin-bottom:8px">⚡ SOLARPUNK NANOSHOP</div>',

        /* title */
        '<div style="font-size:14px;font-weight:700;line-height:1.3;margin-bottom:4px;padding-right:20px">' + title + '</div>',

        /* price */
        '<div style="font-size:22px;font-weight:900;color:#c8a86b;margin:6px 0">$' + price + '</div>',

        /* gaza */
        gazaBar(gaza),

        /* buy button */
        '<a id="sp-buy" href="' + paypal + '" target="_blank" rel="noopener" style="',
          'display:block;background:#c8a86b;color:#080808;',
          'text-align:center;text-decoration:none;font-weight:800;',
          'font-size:14px;border-radius:8px;padding:10px;margin-top:12px;',
          'transition:background .2s" ',
          'onmouseover="this.style.background=\'#dfc07d\'" ',
          'onmouseout="this.style.background=\'#c8a86b\'">',
          'Buy Now — $' + price + ' via PayPal',
        '</a>',

        /* gumroad optional */
        gumroad ? '<a href="' + gumroad + '" target="_blank" rel="noopener" style="' +
          'display:block;text-align:center;font-size:11px;color:rgba(255,255,255,.35);' +
          'margin-top:6px;text-decoration:none" ' +
          'onmouseover="this.style.color=\'rgba(255,255,255,.7)\'" ' +
          'onmouseout="this.style.color=\'rgba(255,255,255,.35)\'">or Gumroad</a>' : '',

        /* footer */
        '<div style="text-align:center;font-size:9px;color:rgba(255,255,255,.2);margin-top:10px">',
          '<a href="' + BASE + '/shop.html" target="_blank" ',
             'style="color:rgba(255,255,255,.2);text-decoration:none" ',
             'onmouseover="this.style.color=\'rgba(255,255,255,.5)\'" ',
             'onmouseout="this.style.color=\'rgba(255,255,255,.2)\'">View full shop</a>',
        '</div>',

      '</div>',
    ].join('');

    return el;
  }

  // ─── Inject CSS keyframe ──────────────────────────────────────────────────────
  function injectCSS() {
    if (document.getElementById('sp-nanoshop-css')) return;
    var s = document.createElement('style');
    s.id = 'sp-nanoshop-css';
    s.textContent = '@keyframes sp-fadein{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}';
    document.head.appendChild(s);
  }

  // ─── Show ─────────────────────────────────────────────────────────────────────
  function show(product) {
    if (isDismissed()) return;
    if (document.getElementById('sp-nanoshop')) return;

    injectCSS();
    var widget = buildWidget(product);
    document.body.appendChild(widget);

    // Close on × click
    document.getElementById('sp-x').addEventListener('click', function() {
      markDismissed();
      hide();
    });

    // Close on buy click (after opening)
    var buyBtn = document.getElementById('sp-buy');
    if (buyBtn) {
      buyBtn.addEventListener('click', function() {
        setTimeout(function() { hide(); }, 800);
      });
    }

    // Close on outside click
    document.addEventListener('click', function outsideClick(e) {
      var w = document.getElementById('sp-nanoshop');
      if (w && !w.contains(e.target)) {
        markDismissed();
        hide();
        document.removeEventListener('click', outsideClick);
      }
    });
  }

  function hide() {
    var w = document.getElementById('sp-nanoshop');
    if (w) {
      w.style.opacity = '0';
      w.style.transition = 'opacity .25s';
      setTimeout(function() { if (w.parentNode) w.parentNode.removeChild(w); }, 260);
    }
  }

  // ─── Auto-load product ────────────────────────────────────────────────────────
  function autoLoad() {
    // If product already configured inline, use it immediately
    if (config.title && config.price && config.paypal) {
      setTimeout(function() { show(config); }, config.delay);
      return;
    }
    // Otherwise fetch index and pick a product
    fetch(INDEX_URL)
      .then(function(r) { return r.json(); })
      .then(function(data) {
        var products = data.products || [];
        if (!products.length) return;
        // Rotate by day
        var idx = Math.floor(Date.now() / 86400000) % products.length;
        var product = products[idx];
        setTimeout(function() { show(product); }, config.delay);
      })
      .catch(function() {
        // Fallback hardcoded product
        setTimeout(function() {
          show({
            title: 'Build Your Own SolarPunk — Complete Guide',
            price: '1.00',
            paypal: 'https://www.paypal.me/meekotharaccoon/1USD',
            gaza: '15',
          });
        }, config.delay);
      });
  }

  // ─── Public API ──────────────────────────────────────────────────────────────
  window.SolarPunkNanoshop = { show: show, hide: hide };

  // ─── Auto-init ───────────────────────────────────────────────────────────────
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoLoad);
  } else {
    autoLoad();
  }

})();
