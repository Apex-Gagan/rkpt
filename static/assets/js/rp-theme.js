/* ==========================================================================
   RAKESH PACKERS — storefront interactions (vanilla JS, no dependencies)
   ========================================================================== */
(function () {
    'use strict';

    /* ---------- helpers ---------- */
    function $(sel, ctx) { return (ctx || document).querySelector(sel); }

    function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

    function getCookie(name) {
        var val = null;
        if (document.cookie) {
            document.cookie.split(';').forEach(function (c) {
                c = c.trim();
                if (c.indexOf(name + '=') === 0) val = decodeURIComponent(c.slice(name.length + 1));
            });
        }
        return val;
    }

    window.rpGetCookie = getCookie;

    /* ---------- toast ---------- */
    var toastTimer = null;

    window.rpToast = function (msg, icon) {
        var t = $('#rp-toast');
        if (!t) return;
        t.innerHTML = '<i class="' + (icon || 'fa-solid fa-circle-check') + '"></i><span></span>';
        t.querySelector('span').textContent = msg;
        t.classList.add('show');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(function () { t.classList.remove('show'); }, 3200);
    };

    /* ---------- cart badge ---------- */
    window.rpSetCartCount = function (n) {
        $$('.js-cart-count').forEach(function (b) {
            b.textContent = n;
            b.style.display = n > 0 ? '' : 'none';
            b.classList.remove('pop');
            void b.offsetWidth; /* restart animation */
            b.classList.add('pop');
        });
    };

    /* ---------- header scroll state ---------- */
    var header = $('.rp-header');
    if (header) {
        var onScroll = function () {
            header.classList.toggle('scrolled', window.scrollY > 8);
        };
        window.addEventListener('scroll', onScroll, {passive: true});
        onScroll();
    }

    /* ---------- desktop dropdowns ---------- */
    $$('.rp-nav .nav-item.has-drop').forEach(function (item) {
        var closeTimer;
        item.addEventListener('mouseenter', function () {
            clearTimeout(closeTimer);
            item.classList.add('open');
        });
        item.addEventListener('mouseleave', function () {
            closeTimer = setTimeout(function () { item.classList.remove('open'); }, 140);
        });
    });

    /* ---------- mobile drawer ---------- */
    var burger = $('#rp-burger');
    var drawerClose = $('#rp-drawer-close');
    var drawerOverlay = $('#rp-drawer-overlay');

    function toggleDrawer(open) {
        document.body.classList.toggle('drawer-open', open);
    }

    if (burger) burger.addEventListener('click', function () { toggleDrawer(true); });
    if (drawerClose) drawerClose.addEventListener('click', function () { toggleDrawer(false); });
    if (drawerOverlay) drawerOverlay.addEventListener('click', function () { toggleDrawer(false); });

    $$('.dr-link.has-sub').forEach(function (link) {
        link.addEventListener('click', function (e) {
            e.preventDefault();
            var sub = link.nextElementSibling;
            if (sub) sub.classList.toggle('openned');
            var ic = link.querySelector('i');
            if (ic) ic.style.transform = sub && sub.classList.contains('openned') ? 'rotate(180deg)' : '';
        });
    });

    /* ---------- generic slider engine (hero + testimonials) ---------- */
    function makeSlider(opts) {
        var slides = $$(opts.slide);
        if (!slides.length) return null;
        var dots = opts.dots ? $$(opts.dots) : [];
        var idx = 0, timer = null;
        var interval = opts.interval || 6000;

        function go(n, user) {
            slides[idx].classList.remove('active');
            if (dots[idx]) dots[idx].classList.remove('active');
            idx = (n + slides.length) % slides.length;
            slides[idx].classList.add('active');
            if (dots[idx]) dots[idx].classList.add('active');
            if (user) restart();
        }

        function next() { go(idx + 1); }

        function restart() {
            clearInterval(timer);
            if (opts.autoplay !== false) timer = setInterval(next, interval);
        }

        dots.forEach(function (d, i) {
            d.addEventListener('click', function () { go(i, true); });
        });
        if (opts.prev) {
            var pv = $(opts.prev);
            if (pv) pv.addEventListener('click', function () { go(idx - 1, true); });
        }
        if (opts.next) {
            var nx = $(opts.next);
            if (nx) nx.addEventListener('click', function () { go(idx + 1, true); });
        }

        /* touch swipe */
        var wrap = opts.swipeEl ? $(opts.swipeEl) : null;
        if (wrap) {
            var sx = 0;
            wrap.addEventListener('touchstart', function (e) { sx = e.touches[0].clientX; }, {passive: true});
            wrap.addEventListener('touchend', function (e) {
                var dx = e.changedTouches[0].clientX - sx;
                if (Math.abs(dx) > 46) go(dx > 0 ? idx - 1 : idx + 1, true);
            }, {passive: true});
        }

        restart();
        return {go: go};
    }

    makeSlider({
        slide: '.hero-slide',
        dots: '.hero-controls .hero-dot',
        prev: '#hero-prev',
        next: '#hero-next',
        swipeEl: '.rp-hero',
        interval: 6000
    });

    makeSlider({
        slide: '.testi-slide',
        dots: '.testi-dot',
        swipeEl: '.testi-wrap',
        interval: 7000
    });

    /* ---------- scroll reveal ---------- */
    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) {
                    en.target.classList.add('in');
                    io.unobserve(en.target);
                }
            });
        }, {threshold: 0.12, rootMargin: '0px 0px -40px 0px'});
        $$('.rv').forEach(function (el) { io.observe(el); });
    } else {
        $$('.rv').forEach(function (el) { el.classList.add('in'); });
    }

    /* ---------- animated counters ---------- */
    function animateCount(el) {
        var target = parseFloat(el.dataset.count || '0');
        var suffix = el.dataset.suffix || '';
        var dur = 1800, t0 = null;

        function frame(t) {
            if (!t0) t0 = t;
            var p = Math.min((t - t0) / dur, 1);
            var eased = 1 - Math.pow(1 - p, 3);
            el.firstChild.nodeValue = Math.round(target * eased).toLocaleString('en-IN');
            if (p < 1) requestAnimationFrame(frame);
        }

        el.innerHTML = '0<span>' + suffix + '</span>';
        requestAnimationFrame(frame);
    }

    if ('IntersectionObserver' in window) {
        var cio = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                if (en.isIntersecting) {
                    animateCount(en.target);
                    cio.unobserve(en.target);
                }
            });
        }, {threshold: 0.4});
        $$('[data-count]').forEach(function (el) { cio.observe(el); });
    }

    /* ---------- WhatsApp widget ---------- */
    var WA_NUMBER = '919988775163';
    var waFab = $('#wa-fab'), waPop = $('#wa-pop'), waClose = $('#wa-pop-close'),
        waSend = $('#wa-pop-send'), waMsg = $('#wa-pop-msg');

    if (waFab) {
        waFab.addEventListener('click', function () { waPop.classList.toggle('show'); });
        waClose.addEventListener('click', function () { waPop.classList.remove('show'); });
        waSend.addEventListener('click', function () {
            var m = waMsg.value.trim();
            if (!m) { waMsg.focus(); return; }
            var full = '*New Message from Website*\n\n*Page:* ' + document.title +
                '\n*Link:* ' + location.href + '\n\n*Message:*\n' + m;
            window.open('https://wa.me/' + WA_NUMBER + '?text=' + encodeURIComponent(full), '_blank', 'noopener');
            waMsg.value = '';
            waPop.classList.remove('show');
        });
        document.addEventListener('click', function (e) {
            if (waPop.classList.contains('show') && !waPop.contains(e.target) && e.target !== waFab && !waFab.contains(e.target)) {
                waPop.classList.remove('show');
            }
        });
    }

    /* ---------- add-to-cart (shared) ---------- */
    window.rpAddToCart = function (productId, qty, onDone) {
        return fetch('/cart/add/', {
            method: 'POST',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: 'product_id=' + encodeURIComponent(productId) + '&qty=' + encodeURIComponent(qty || 1)
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) window.rpSetCartCount(data.cart_count);
                if (onDone) onDone(data);
                return data;
            });
    };

    /* ---------- lightbox (product gallery) ---------- */
    var lb = $('#rp-lightbox');
    if (lb) {
        var lbImg = lb.querySelector('img');
        var lbSources = [];
        var lbIdx = 0;

        window.rpOpenLightbox = function (sources, startIdx) {
            lbSources = sources;
            lbIdx = startIdx || 0;
            lbImg.src = lbSources[lbIdx];
            lb.classList.add('show');
            document.body.style.overflow = 'hidden';
        };

        function lbClose() {
            lb.classList.remove('show');
            document.body.style.overflow = '';
        }

        function lbGo(d) {
            if (!lbSources.length) return;
            lbIdx = (lbIdx + d + lbSources.length) % lbSources.length;
            lbImg.src = lbSources[lbIdx];
        }

        lb.querySelector('.lb-close').addEventListener('click', lbClose);
        lb.querySelector('.lb-prev').addEventListener('click', function () { lbGo(-1); });
        lb.querySelector('.lb-next').addEventListener('click', function () { lbGo(1); });
        lb.addEventListener('click', function (e) { if (e.target === lb) lbClose(); });
        document.addEventListener('keydown', function (e) {
            if (!lb.classList.contains('show')) return;
            if (e.key === 'Escape') lbClose();
            if (e.key === 'ArrowLeft') lbGo(-1);
            if (e.key === 'ArrowRight') lbGo(1);
        });
    }

    /* ---------- category filter (homepage products) ---------- */
    var catBar = $('#cat-bar');
    var catStrip = $('#cat-tabs');
    var catBlocks = $$('.cat-block');

    if (catBar && catStrip && catBlocks.length) {
        var catTabs = $$('.cat-tab', catBar);
        var reduceMotion = window.matchMedia
            && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        var scrollMode = reduceMotion ? 'auto' : 'smooth';
        var catSummary = $('#cat-summary');
        var catPrev = $('#cat-prev'), catNext = $('#cat-next');
        var totalProducts = catBlocks.reduce(function (n, b) {
            return n + b.querySelectorAll('.pcard').length;
        }, 0);

        /* --- arrows --- */
        function syncArrows() {
            var max = catStrip.scrollWidth - catStrip.clientWidth;
            var x = catStrip.scrollLeft;
            var atStart = x <= 1, atEnd = x >= max - 1;
            catStrip.classList.toggle('at-start', atStart);
            catStrip.classList.toggle('at-end', atEnd);
            if (catPrev) catPrev.disabled = atStart;
            if (catNext) catNext.disabled = atEnd;
        }

        function nudge(dir) {
            catStrip.scrollBy({left: dir * Math.max(catStrip.clientWidth * 0.8, 160), behavior: scrollMode});
        }

        if (catPrev) catPrev.addEventListener('click', function () { nudge(-1); });
        if (catNext) catNext.addEventListener('click', function () { nudge(1); });
        catStrip.addEventListener('scroll', syncArrows, {passive: true});
        window.addEventListener('resize', syncArrows);
        syncArrows();

        /* --- filtering --- */
        function scrollToEl(el) {
            if (!el) return;
            var hdr = $('#rp-header');
            var offset = (hdr ? hdr.offsetHeight : 74) + 110;
            var top = el.getBoundingClientRect().top + window.pageYOffset - offset;
            window.scrollTo({top: Math.max(top, 0), behavior: scrollMode});
        }

        function setCategory(key, scroll) {
            var known = key === 'all' || catBlocks.some(function (b) { return b.dataset.cat === key; });
            if (!known) key = 'all';

            catTabs.forEach(function (t) { t.classList.toggle('active', t.dataset.cat === key); });

            var shown = 0;
            catBlocks.forEach(function (b) {
                var wasHidden = b.hidden;
                var show = key === 'all' || b.dataset.cat === key;
                b.hidden = !show;
                if (!show) return;
                shown += b.querySelectorAll('.pcard').length;
                // un-fade only blocks coming back from display:none — on first
                // paint nothing is hidden, so the reveal animation still plays
                if (wasHidden) $$('.rv', b).forEach(function (el) { el.classList.add('in'); });
            });

            if (catSummary) {
                catSummary.innerHTML = key === 'all'
                    ? 'Showing <b>all ' + totalProducts + ' products</b> across ' + catBlocks.length + ' categories'
                    : 'Showing <b>' + shown + ' product' + (shown === 1 ? '' : 's') + '</b> in this category · '
                      + '<a href="#products" data-cat-link="all">see all ' + totalProducts + '</a>';
            }

            var active = catTabs.filter(function (t) { return t.dataset.cat === key; })[0];
            // only pills inside the scrolling strip need bringing into view
            if (active && active.parentNode === catStrip && catStrip.scrollTo) {
                catStrip.scrollTo({
                    left: Math.max(active.offsetLeft - (catStrip.clientWidth - active.offsetWidth) / 2, 0),
                    behavior: scrollMode
                });
            }

            if (scroll) scrollToEl(key === 'all' ? $('#products') : document.getElementById(key));
        }

        catTabs.forEach(function (t) {
            t.addEventListener('click', function () {
                // keep the URL shareable without stacking history entries
                if (history.replaceState) {
                    history.replaceState(null, '', t.dataset.cat === 'all'
                        ? location.pathname + location.search
                        : '#' + t.dataset.cat);
                }
                setCategory(t.dataset.cat, true);
            });
        });

        // category cards (and the summary's "see all") deep-link into a category
        document.addEventListener('click', function (e) {
            var link = e.target.closest ? e.target.closest('[data-cat-link]') : null;
            if (!link) return;
            e.preventDefault();
            var key = link.dataset.catLink;
            if (history.replaceState) {
                history.replaceState(null, '', key === 'all'
                    ? location.pathname + location.search
                    : '#' + key);
            }
            setCategory(key, true);
        });

        function categoryFromHash() {
            var hash = (location.hash || '').replace('#', '');
            if (hash.indexOf('cat-') === 0) setCategory(hash, true);
        }

        window.addEventListener('hashchange', categoryFromHash);

        setCategory('all', false);
        categoryFromHash();
    }

    /* ---------- hover zoom on product main image ---------- */
    var zoomBox = $('.pd-main');
    if (zoomBox && window.matchMedia('(hover: hover)').matches) {
        var zImg = zoomBox.querySelector('img');
        zoomBox.addEventListener('mousemove', function (e) {
            var r = zoomBox.getBoundingClientRect();
            var x = ((e.clientX - r.left) / r.width) * 100;
            var y = ((e.clientY - r.top) / r.height) * 100;
            zImg.style.transformOrigin = x + '% ' + y + '%';
            zImg.style.transform = 'scale(1.9)';
        });
        zoomBox.addEventListener('mouseleave', function () {
            zImg.style.transform = '';
            zImg.style.transformOrigin = 'center';
        });
    }
})();
