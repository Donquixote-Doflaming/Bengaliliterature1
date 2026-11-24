/* ==========================================================================
   বাংলা সাহিত্য — shared behaviour
   loader · theme · grid overlay · search · toast
   ========================================================================== */
(function () {
  'use strict';

  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.prototype.slice.call((r || document).querySelectorAll(s));
  const BENG_DIGITS = ['০', '১', '২', '৩', '৪', '৫', '৬', '৭', '৮', '৯'];

  /* convert 123 -> "১২৩" */
  function bn(n) {
    return String(n).split('').map(c => (c >= '0' && c <= '9' ? BENG_DIGITS[+c] : c)).join('');
  }
  function pad2(n) { return (n < 10 ? '0' : '') + n; }

  /* ---------------------------------------------------------------- theme */
  const THEME_KEY = 'bangla-lit-theme';
  function applyTheme(t) {
    if (t === 'dark') document.documentElement.setAttribute('data-theme', 'dark');
    else document.documentElement.removeAttribute('data-theme');
    $$('[data-theme-toggle]').forEach(b => {
      b.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
      b.setAttribute('aria-label', t === 'dark' ? 'আলো মোড' : 'অন্ধকার মোড');
    });
  }
  function initTheme() {
    let t = null;
    try { t = localStorage.getItem(THEME_KEY); } catch (e) { /* private mode */ }
    /* Light is the house default — the OS preference is deliberately ignored
       so a dark-mode device still lands on the paper-white board. The user can
       still switch, and that choice is remembered. */
    if (t !== 'dark' && t !== 'light') t = 'light';
    applyTheme(t);
    document.addEventListener('click', e => {
      const b = e.target.closest('[data-theme-toggle]');
      if (!b) return;
      const next = document.documentElement.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      try { localStorage.setItem(THEME_KEY, next); } catch (err) { /* ignore */ }
      toast(next === 'dark' ? 'অন্ধকার মোড' : 'আলো মোড');
    });
  }

  /* --------------------------------------------------------- text size */
  /* Three steps: default -> large -> extra large. The scale lives in CSS as
     --ts on :root, so every rule that reads it grows together. */
  const SIZE_KEY = 'bangla-lit-size';
  const SIZES = ['', 'lg', 'xl'];
  const SIZE_LABEL = { '': 'সাধারণ', lg: 'বড়', xl: 'সবচেয়ে বড়' };

  function applySize(s) {
    if (s) document.documentElement.setAttribute('data-size', s);
    else document.documentElement.removeAttribute('data-size');
    const i = SIZES.indexOf(s);
    $$('[data-size-toggle]').forEach(b => {
      b.setAttribute('aria-pressed', s ? 'true' : 'false');
      b.setAttribute('aria-label', 'লেখার আকার — ' + SIZE_LABEL[SIZES[i]]);
      const cur = b.querySelector('b');
      if (cur) cur.textContent = ['ক', 'ক', 'ক'][i] || 'ক';
      const st = b.querySelector('i');
      if (st) st.textContent = ['S', 'M', 'L'][i] || 'S';
    });
  }

  function initSize() {
    let s = null;
    try { s = localStorage.getItem(SIZE_KEY); } catch (e) { /* private mode */ }
    if (SIZES.indexOf(s) === -1) s = '';
    applySize(s);
    document.addEventListener('click', e => {
      const b = e.target.closest('[data-size-toggle]');
      if (!b) return;
      const cur = document.documentElement.getAttribute('data-size') || '';
      const next = SIZES[(SIZES.indexOf(cur) + 1) % SIZES.length];
      applySize(next);
      try { localStorage.setItem(SIZE_KEY, next); } catch (err) { /* ignore */ }
      toast('লেখার আকার: ' + SIZE_LABEL[next]);
    });
    /* keyboard: - and = to shrink / grow */
    document.addEventListener('keydown', e => {
      if (/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key !== '-' && e.key !== '=' && e.key !== '+') return;
      const cur = document.documentElement.getAttribute('data-size') || '';
      let i = SIZES.indexOf(cur);
      i = e.key === '-' ? Math.max(0, i - 1) : Math.min(SIZES.length - 1, i + 1);
      if (i === SIZES.indexOf(cur)) return;
      e.preventDefault();
      applySize(SIZES[i]);
      try { localStorage.setItem(SIZE_KEY, SIZES[i]); } catch (err) { /* ignore */ }
      toast('লেখার আকার: ' + SIZE_LABEL[SIZES[i]]);
    });
  }

  /* ------------------------------------------------------------ grid overlay */
  function initGrid() {
    const cols = $('#grid-cols');
    if (cols) {
      for (let i = 0; i < 12; i++) {
        const el = document.createElement('i');
        el.style.setProperty('--i', i);
        el.innerHTML = '<b>' + pad2(i + 1) + '</b>';
        cols.appendChild(el);
      }
      const spec = $('#grid-spec');
      if (spec) spec.textContent = '12 col / 16 px col / 0 px gutter / 12 px margin';
    }
    document.addEventListener('keydown', e => {
      if (e.key === 'g' && !/^(INPUT|TEXTAREA)$/.test(document.activeElement.tagName) && !e.metaKey && !e.ctrlKey) {
        e.preventDefault();
        toggleGrid();
      }
    });
    document.addEventListener('click', e => {
      const b = e.target.closest('[data-grid-toggle]');
      if (b) { toggleGrid(); return; }
    });
  }
  function toggleGrid() {
    const on = document.body.classList.toggle('grid-on');
    $$('[data-grid-toggle]').forEach(b => b.setAttribute('aria-pressed', on ? 'true' : 'false'));
  }

  /* ----------------------------------------------------------------- toast */
  let toastEl, toastTimer;
  function toast(msg) {
    if (!toastEl) {
      toastEl = document.createElement('div');
      toastEl.className = 'toast';
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add('on');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove('on'), 1600);
  }

  /* ---------------------------------------------------------------- loader */
  function initLoader() {
    const loader = $('#loader');
    if (!loader) { document.body.classList.add('loaded'); return; }

    const field = $('#ld-field');
    const num = $('#ld-num');
    if (field) {
      for (let i = 0; i < 12; i++) {
        const t = document.createElement('div');
        t.className = 'ld-tile';
        t.style.gridColumn = (i + 1);
        t.style.gridRow = '1 / -1';
        t.style.setProperty('--d', (i * 0.035).toFixed(3) + 's');
        field.appendChild(t);
      }
    }
    const ld = $('#ld-count');
    if (ld && !field) ld.hidden = false;

    let pct = 0;
    let done = false;
    const start = performance.now();

    const tick = () => {
      if (done) return;
      const elapsed = performance.now() - start;
      const target = Math.min(92, 8 + (elapsed / 1100) * 84);
      pct += (target - pct) * 0.14;
      if (num) num.textContent = Math.round(pct);
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);

    const finish = () => {
      if (done) return;
      done = true;
      if (num) {
        let v = Math.round(pct);
        const step = () => {
          v += Math.max(1, Math.round((100 - v) / 4));
          if (v > 100) v = 100;
          num.textContent = v;
          if (v < 100) setTimeout(step, 55);
          else setTimeout(hide, 240);
        };
        step();
      } else hide();
    };

    const hide = () => {
      loader.classList.add('out');
      document.body.classList.remove('locked');
      document.body.classList.add('loaded');
      setTimeout(() => { loader.hidden = true; }, 480);
    };

    if (document.readyState === 'complete') setTimeout(finish, 260);
    else window.addEventListener('load', () => setTimeout(finish, 260));
    setTimeout(() => { if (!done) finish(); }, 4000);
  }

  /* strip markup so the search index stays plain text */
  function textOf(html) {
    if (!html) return '';
    return html.join(' ')
      .replace(/<[^>]+>/g, ' ')
      .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&')
      .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
      .replace(/\s+/g, ' ').trim();
  }

  /* ---------------------------------------------------------------- search */
  const Search = {
    el: null, input: null, results: null, idx: null, activeLetter: null, q: '',
    /* exposed so other pages can reuse the shared toast */
    toast,

    mount() {
      this.el = $('#search');
      if (!this.el) return;
      this.input = $('#search-input');
      this.results = $('#search-results');
      this.buildAz();

      this.input.addEventListener('input', () => { this.q = this.input.value.trim(); this.render(); });
      $('#search-close').addEventListener('click', () => this.close());
      this.el.addEventListener('click', e => { if (e.target === this.el) this.close(); });

      /* Clicking a result must leave the search and go to that result.
         Close the overlay first, then let the browser follow the link —
         but same-page targets need an explicit scroll because the sticky
         header would otherwise cover the heading. */
      this.results.addEventListener('click', e => {
        const a = e.target.closest('a');
        if (!a) return;
        const href = a.getAttribute('href') || '';
        const m = /^#(.+)$/.exec(href);
        if (!m) { this.close(); return; }        /* cross-page: plain navigation */
        e.preventDefault();
        this.close();
        const frag = m[1];
        const target = document.getElementById(frag);
        if (!target) {
          /* No element with that id (a quiz question, for example): let the
             page handle the hash itself. */
          if (location.hash !== '#' + frag) {
            location.hash = frag;
          } else {
            window.dispatchEvent(new HashChangeEvent('hashchange'));
          }
          return;
        }
        const top = target.getBoundingClientRect().top + window.scrollY - 92;
        /* A smooth scroll across a whole long document takes seconds, so
           jump instantly when the target is far away. */
        const far = Math.abs(top - window.scrollY) > window.innerHeight * 3;
        window.scrollTo({ top: Math.max(0, top), behavior: far ? 'instant' : 'smooth' });
        history.replaceState(null, '', '#' + frag);
        target.setAttribute('tabindex', '-1');
        target.focus({ preventScroll: true });
      });

      document.addEventListener('keydown', e => {
        if ((e.key === 'k' || e.key === 'K') && (e.metaKey || e.ctrlKey)) {
          e.preventDefault(); this.toggle();
        }
        if (e.key === 'Escape' && this.el.classList.contains('on')) this.close();
      });
      document.addEventListener('click', e => {
        const b = e.target.closest('[data-search-open]');
        if (b) { e.preventDefault(); this.toggle(); }
      });
    },

    buildAz() {
      const az = $('#search-az');
      if (!az) return;
      const letters = 'অআইঈউঊঋএঐওঔকখগঘঙচছজঝঞটঠডঢণতথদধনপফবভমযরলশষসহ';
      letters.split('').forEach(L => {
        const b = document.createElement('button');
        b.type = 'button';
        b.textContent = L;
        b.addEventListener('click', () => {
          if (this.activeLetter === L) {
            this.activeLetter = null;
            b.classList.remove('on');
          } else {
            this.activeLetter = L;
            $$('#search-az button').forEach(x => x.classList.remove('on'));
            b.classList.add('on');
          }
          this.render();
        });
        az.appendChild(b);
      });
    },

    open() {
      this.el.classList.add('on');
      document.body.style.overflow = 'hidden';
      this.buildIndex();
      setTimeout(() => this.input.focus(), 90);
      this.render();
    },
    close() {
      this.el.classList.remove('on');
      document.body.style.overflow = '';
    },
    toggle() { this.el.classList.contains('on') ? this.close() : this.open(); },

    buildIndex() {
      if (this.idx) return;
      const R = window.READ || { sections: [], authors: [], readings: [] };
      const Q = window.QUIZ || [];
      this.idx = [];

      (R.sections || []).forEach(sec => {
        this.idx.push({ kind: 'অংশ', id: sec.id, title: sec.title, text: textOf(sec.html) });
        (sec.subs || []).forEach(sub => {
          this.idx.push({ kind: 'উপঅংশ', id: sub.id, title: sec.title + ' › ' + sub.title, text: textOf(sub.html) });
          (sub.subs || []).forEach(s2 => {
            this.idx.push({ kind: 'উপঅংশ', id: s2.id, title: sec.title + ' › ' + sub.title + ' › ' + s2.title, text: textOf(s2.html) });
          });
        });
      });
      (R.authors || []).forEach(a => {
        this.idx.push({ kind: 'লেখক', id: a.id, title: a.name, text: a.tagline + ' ' + textOf(a.html) });
      });
      (R.readings || []).forEach(r => {
        this.idx.push({ kind: 'পাঠ', id: r.id, title: r.title, text: r.tagline + ' ' + textOf(r.html) });
      });
      /* Question links are one-based: quiz.html#q1 is the first question.
         The index below is zero-based, so add one when the link is built. */
      Q.forEach((q, i) => {
        this.idx.push({ kind: 'প্রশ্ন', id: 'q' + (i + 1), title: q.q, text: q.a, q: i + 1 });
      });
      this.idx.forEach(e => { e._t = (e.title + ' ' + e.text).toLowerCase(); });
    },

    score(item) {
      const q = this.q.toLowerCase();
      if (!q) return 0;
      const t = item._t;
      let i = t.indexOf(q);
      if (i < 0) return -1;
      let s = 100 - i / 40;
      if (item.title.toLowerCase().startsWith(q)) s += 60;
      return s;
    },

    render() {
      if (!this.results) return;
      const q = this.q.toLowerCase();
      const L = this.activeLetter;
      let list;
      if (!q && !L) {
        this.results.innerHTML = '<p class="none">লেখকের নাম, বইয়ের নাম বা সাল লিখে খুঁজুন।</p>';
        return;
      }
      list = [];
      for (const it of this.idx) {
        if (L && it.title.indexOf(L) !== 0) continue;
        const sc = this.score(it);
        if (sc < 0) continue;
        list.push({ it: it, sc: sc });
      }
      list.sort((a, b) => b.sc - a.sc);
      list = list.slice(0, 60);
      if (!list.length) {
        this.results.innerHTML = '<p class="none">কিছু মেলেনি। অন্য শব্দ দিয়ে চেষ্টা করুন।</p>';
        return;
      }
      const hl = s => q ? s.replace(new RegExp('(' + q.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + ')', 'gi'), '<mark>$1</mark>') : s;
      /* Results may point at a heading on this page, at a heading on the
         other page, or at a quiz question. Build the href for the page we
         are actually on so same-page targets stay in-page and the browser
         can scroll to them. */
      const here = location.pathname.split('/').pop() || 'index.html';
      const urlFor = it => {
        if (it.q !== undefined) {
          /* quiz question — #qN is one-based (quiz.html#q1 == first question) */
          return here === 'quiz.html' ? '#q' + it.q : 'quiz.html#q' + it.q;
        }
        return here === 'study.html' ? '#' + it.id : 'study.html#' + it.id;
      };
      this.results.innerHTML = '<ol>' + list.map(r =>
        '<li><a href="' + urlFor(r.it) + '">' +
        '<span class="rk">' + r.it.kind + '</span>' +
        '<span class="rt">' + hl(r.it.title) + '</span>' +
        '<span class="rs">' + hl((r.it.text || '').slice(0, 190)) + '</span></a></li>'
      ).join('') + '</ol>';
    }
  };

  /* ------------------------------------------------------------------ init */
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initSize();
    initGrid();
    initLoader();
    Search.mount();
    window.Search = Search;
  });
})();
