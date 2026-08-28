/* ==========================================================================
   RAKESH PACKERS — motion layer (vanilla JS, no dependencies)

   Loads after rp-theme.js and layers on the effects that need per-element
   measurement: split-heading reveals, pointer tilt, scroll progress, and the
   product page's sticky order bar. Everything here is decorative — if it is
   skipped (reduced motion, no IntersectionObserver, coarse pointer) the page
   still reads and works exactly the same.
   ========================================================================== */
(function () {
    'use strict';

    function $(sel, ctx) { return (ctx || document).querySelector(sel); }

    function $$(sel, ctx) { return Array.prototype.slice.call((ctx || document).querySelectorAll(sel)); }

    var reduceMotion = window.matchMedia
        && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var finePointer = window.matchMedia
        && window.matchMedia('(hover: hover) and (pointer: fine)').matches;
    var hasIO = 'IntersectionObserver' in window;

    /* ----------------------------------------------------------------------
       Split headings into masked words
       ---------------------------------------------------------------------- */

    /* Walks the heading's own child nodes so nested markup — the italic accent
       span, a <br> — survives the split. Text becomes one `.sp-w` per word;
       any element child is wrapped whole. */
    function splitWords(el) {
        if (el.dataset.split === 'done') return;
        var out = document.createDocumentFragment();
        var i = 0;

        function wrap(node) {
            var w = document.createElement('span');
            w.className = 'sp-w';
            var inner = document.createElement('span');
            inner.style.setProperty('--i', i++);
            inner.appendChild(node);
            w.appendChild(inner);
            return w;
        }

        Array.prototype.slice.call(el.childNodes).forEach(function (node) {
            if (node.nodeType === 3) {
                var parts = node.nodeValue.split(/(\s+)/);
                parts.forEach(function (part) {
                    if (!part) return;
                    if (/^\s+$/.test(part)) {
                        out.appendChild(document.createTextNode(' '));
                    } else {
                        out.appendChild(wrap(document.createTextNode(part)));
                    }
                });
            } else if (node.nodeType === 1) {
                out.appendChild(wrap(node.cloneNode(true)));
            }
        });

        el.innerHTML = '';
        el.appendChild(out);
        el.classList.add('sp');
        el.dataset.split = 'done';
    }

    var SPLIT_TARGETS = '.hero-title, .sec-title, .band-title, .pd-title, .cart-head h1, .ct-hero h1';
    var splitEls = $$(SPLIT_TARGETS);

    if (!reduceMotion) {
        splitEls.forEach(splitWords);

        if (hasIO) {
            var spIO = new IntersectionObserver(function (entries) {
                entries.forEach(function (en) {
                    // Hero titles live inside a slider; they are driven by slide
                    // state below, not by visibility.
                    if (en.isIntersecting && !en.target.closest('.hero-slide')) {
                        en.target.classList.add('in');
                        spIO.unobserve(en.target);
                    }
                });
            }, {threshold: 0.2, rootMargin: '0px 0px -60px 0px'});
            splitEls.forEach(function (el) { spIO.observe(el); });
        } else {
            splitEls.forEach(function (el) { el.classList.add('in'); });
        }

        /* Hero titles replay each time their slide comes round. rp-theme.js owns
           the slider, so watch the class it toggles rather than reaching into it. */
        var heroSlides = $$('.hero-slide');
        if (heroSlides.length && 'MutationObserver' in window) {
            // Each slide owns its own title, so the outgoing one resets while
            // the incoming one reveals — no need to wait a frame between the
            // two, and no rAF that would stall in a background tab and leave
            // the headline invisible.
            var syncSlide = function (slide) {
                var title = $('.hero-title', slide);
                if (title) title.classList.toggle('in', slide.classList.contains('active'));
            };
            var slideMO = new MutationObserver(function (records) {
                records.forEach(function (r) { syncSlide(r.target); });
            });
            heroSlides.forEach(function (s) {
                slideMO.observe(s, {attributes: true, attributeFilter: ['class']});
                syncSlide(s);
            });
        }
    }

    /* ----------------------------------------------------------------------
       Reveal stagger — index within the container, not a fixed nth-child
       ---------------------------------------------------------------------- */
    ['.prod-grid', '.cat-scroll', '.usp-grid', '.steps-grid', '.ct-cards', '.pd-specs']
        .forEach(function (sel) {
            $$(sel).forEach(function (container) {
                $$(':scope > .rv', container).forEach(function (el, i) {
                    // Cap the ramp so a 20-card grid does not end on a 1.3s delay.
                    el.style.setProperty('--rv-i', Math.min(i, 7));
                    el.classList.add('rv-stagger');
                });
            });
        });

    /* ----------------------------------------------------------------------
       Pointer tilt on product cards
       ---------------------------------------------------------------------- */
    if (finePointer && !reduceMotion) {
        var MAX_TILT = 5; /* degrees — past ~6 it reads as a gimmick */
        $$('.pcard').forEach(function (card) {
            var frame = null;

            card.addEventListener('mousemove', function (e) {
                if (frame) return;
                frame = requestAnimationFrame(function () {
                    frame = null;
                    var r = card.getBoundingClientRect();
                    var x = (e.clientX - r.left) / r.width - 0.5;
                    var y = (e.clientY - r.top) / r.height - 0.5;
                    card.style.setProperty('--tx', (x * MAX_TILT).toFixed(2) + 'deg');
                    card.style.setProperty('--ty', (-y * MAX_TILT).toFixed(2) + 'deg');
                });
            });

            card.addEventListener('mouseleave', function () {
                card.style.setProperty('--tx', '0deg');
                card.style.setProperty('--ty', '0deg');
            });
        });
    }

    /* ----------------------------------------------------------------------
       Hero card parallax
       ---------------------------------------------------------------------- */
    var hero = $('.rp-hero');
    if (hero && finePointer && !reduceMotion) {
        var heroFrame = null;
        hero.addEventListener('mousemove', function (e) {
            if (heroFrame) return;
            heroFrame = requestAnimationFrame(function () {
                heroFrame = null;
                var r = hero.getBoundingClientRect();
                var px = ((e.clientX - r.left) / r.width - 0.5) * 2;
                var py = ((e.clientY - r.top) / r.height - 0.5) * 2;
                $$('.hero-card').forEach(function (c) {
                    c.style.setProperty('--px', px.toFixed(3));
                    c.style.setProperty('--py', py.toFixed(3));
                });
            });
        });
        hero.addEventListener('mouseleave', function () {
            $$('.hero-card').forEach(function (c) {
                c.style.setProperty('--px', 0);
                c.style.setProperty('--py', 0);
            });
        });
    }

    /* ----------------------------------------------------------------------
       Reading progress
       ---------------------------------------------------------------------- */
    var progress = $('#rp-progress span');
    var scrollFrame = null;

    function onScrollFx() {
        if (!progress || scrollFrame) return;
        scrollFrame = requestAnimationFrame(function () {
            scrollFrame = null;
            var max = document.documentElement.scrollHeight - window.innerHeight;
            progress.style.setProperty('--p', max > 0 ? Math.min(window.scrollY / max, 1).toFixed(4) : 0);
        });
    }

    window.addEventListener('scroll', onScrollFx, {passive: true});
    window.addEventListener('resize', onScrollFx);
    onScrollFx();

    /* ----------------------------------------------------------------------
       Product page — sticky order bar
       ---------------------------------------------------------------------- */
    var stickyBar = $('#pd-sticky');
    var buyBox = $('.pd-buy');
    if (stickyBar && buyBox && hasIO) {
        var barIO = new IntersectionObserver(function (entries) {
            entries.forEach(function (en) {
                // Show it once the real buy box has scrolled past, not before.
                stickyBar.classList.toggle('show', !en.isIntersecting && en.boundingClientRect.top < 0);
            });
        }, {threshold: 0});
        barIO.observe(buyBox);

        var stickyBtn = $('#pd-sticky-add');
        var mainBtn = $('#add-to-cart-btn');
        if (stickyBtn && mainBtn) {
            stickyBtn.addEventListener('click', function () { mainBtn.click(); });
        }
    }

    /* ----------------------------------------------------------------------
       Lightbox counter
       rp-theme.js owns the lightbox state, so read the position back off the
       <img> it swaps rather than duplicating the index here.
       ---------------------------------------------------------------------- */
    var lb = $('#rp-lightbox');
    var lbCount = $('#lb-count');
    if (lb && lbCount && typeof window.rpOpenLightbox === 'function') {
        var lbImg = lb.querySelector('img');
        var lbSources = [];

        function paintCount() {
            if (!lbSources.length) { lbCount.textContent = ''; return; }
            var idx = lbSources.indexOf(lbImg.getAttribute('src'));
            lbCount.textContent = (idx < 0 ? 1 : idx + 1) + ' / ' + lbSources.length;
        }

        var openLightbox = window.rpOpenLightbox;
        window.rpOpenLightbox = function (sources, startIdx) {
            lbSources = sources || [];
            openLightbox(sources, startIdx);
            paintCount();
        };

        if ('MutationObserver' in window) {
            new MutationObserver(paintCount)
                .observe(lbImg, {attributes: true, attributeFilter: ['src']});
        }
    }
})();
