/* ==================================================================
 * Linework — main.js
 * Vanilla JavaScript, no jQuery. One function per feature, each with
 * guard clauses so it quietly does nothing on pages without it.
 * ================================================================== */
(function () {
  'use strict';

  var reduced = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
  var ICON_PLUS = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>';
  var ICON_CHECK = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7"/></svg>';
  var ICON_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>';

  function isoDate(d) {
    return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  }

  /* ----------------------------------------------------------------
   * Mobile menu: close after a link is tapped.
   * ---------------------------------------------------------------- */
  function initNav() {
    var collapse = document.getElementById('primary-nav');
    if (!collapse || !window.bootstrap) return;
    collapse.querySelectorAll('a').forEach(function (link) {
      link.addEventListener('click', function () {
        if (!collapse.classList.contains('show')) return;
        var inst = window.bootstrap.Collapse.getInstance(collapse);
        if (inst) inst.hide();
      });
    });
  }

  /* ----------------------------------------------------------------
   * Header gets its outline once the page scrolls.
   * ---------------------------------------------------------------- */
  function initHeaderScroll() {
    var header = document.querySelector('.site-header');
    if (!header) return;
    var onScroll = function () { header.classList.toggle('is-scrolled', window.scrollY > 8); };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  /* ----------------------------------------------------------------
   * Reveal on scroll. Content is visible without JS; .js hides it.
   * ---------------------------------------------------------------- */
  function initReveal() {
    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    if (reduced || !('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('in');
        io.unobserve(entry.target);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
    els.forEach(function (el) { io.observe(el); });
  }

  /* ----------------------------------------------------------------
   * Marquee band: duplicate the list for a seamless loop.
   * ---------------------------------------------------------------- */
  function initMarquee() {
    document.querySelectorAll('.band').forEach(function (band) {
      var track = band.querySelector('.band-track');
      var list = track && track.querySelector('.band-list');
      if (!list) return;
      var clone = list.cloneNode(true);
      clone.setAttribute('aria-hidden', 'true');
      track.appendChild(clone);
      if (!reduced) band.classList.add('is-moving');
    });
  }

  /* ----------------------------------------------------------------
   * Footer year.
   * ---------------------------------------------------------------- */
  function initYear() {
    var year = String(new Date().getFullYear());
    document.querySelectorAll('[data-year]').forEach(function (el) { el.textContent = year; });
  }

  /* ----------------------------------------------------------------
   * Projects: filter the grid by discipline (?d=murals works too).
   * ---------------------------------------------------------------- */
  function initProjectFilters() {
    var buttons = document.querySelectorAll('[data-filter]');
    var items = document.querySelectorAll('.project-grid > li');
    if (!buttons.length || !items.length) return;
    var status = document.querySelector('.filter-status');
    var nouns = { editorial: 'editorial', books: 'book cover', characters: 'character design', murals: 'mural' };

    function apply(filter) {
      var shown = 0;
      buttons.forEach(function (b) { b.setAttribute('aria-pressed', String(b.dataset.filter === filter)); });
      items.forEach(function (li) {
        var match = filter === 'all' || li.dataset.discipline === filter;
        if (!match) { li.hidden = true; return; }
        shown++;
        if (li.hidden) {
          li.hidden = false;
          if (!reduced) {
            li.classList.add('is-entering');
            requestAnimationFrame(function () { requestAnimationFrame(function () { li.classList.remove('is-entering'); }); });
          }
        }
      });
      if (status) {
        status.textContent = filter === 'all'
          ? 'Showing all ' + shown + ' projects.'
          : 'Showing ' + shown + ' ' + nouns[filter] + ' project' + (shown === 1 ? '' : 's') + '.';
      }
    }

    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        apply(b.dataset.filter);
        var url = new URL(window.location.href);
        if (b.dataset.filter === 'all') url.searchParams.delete('d'); else url.searchParams.set('d', b.dataset.filter);
        history.replaceState(null, '', url);
      });
    });

    var initial = new URLSearchParams(window.location.search).get('d');
    if (initial && document.querySelector('[data-filter="' + CSS.escape(initial) + '"]')) apply(initial);
  }

  /* ----------------------------------------------------------------
   * Case-study dialogs. Without JS the same markup opens via :target.
   * ---------------------------------------------------------------- */
  function initCaseDialogs() {
    var dialogs = document.querySelectorAll('dialog.case');
    if (!dialogs.length || typeof HTMLDialogElement !== 'function') return;
    var lastTrigger = null;

    function open(id) {
      var d = document.getElementById(id);
      if (!d || d.open) return;
      d.showModal();
      d.scrollTop = 0;
      document.documentElement.classList.add('has-dialog');
      history.replaceState(null, '', '#' + id);
    }

    function step(from, id) {
      lastTrigger = document.querySelector('[data-case="' + id + '"]') || lastTrigger;
      from.close();
      open(id);
      var close = document.getElementById(id).querySelector('[data-close]');
      if (close) close.focus();
    }

    dialogs.forEach(function (d) {
      d.addEventListener('close', function () {
        if (document.querySelector('dialog.case[open]')) return;
        document.documentElement.classList.remove('has-dialog');
        history.replaceState(null, '', window.location.pathname + window.location.search);
        if (lastTrigger) lastTrigger.focus();
      });
      // click on the backdrop closes
      d.addEventListener('click', function (e) { if (e.target === d) d.close(); });
      d.querySelectorAll('[data-close]').forEach(function (btn) {
        btn.setAttribute('role', 'button');
        btn.addEventListener('click', function (e) { e.preventDefault(); d.close(); });
      });
      d.querySelectorAll('[data-case-link]').forEach(function (a) {
        a.addEventListener('click', function (e) { e.preventDefault(); step(d, a.dataset.caseLink); });
      });
      // arrow keys step through projects
      d.addEventListener('keydown', function (e) {
        if (e.key !== 'ArrowLeft' && e.key !== 'ArrowRight') return;
        var links = d.querySelectorAll('[data-case-link]');
        var target = e.key === 'ArrowLeft' ? links[0] : links[links.length - 1];
        if (target) { e.preventDefault(); step(d, target.dataset.caseLink); }
      });
    });

    document.querySelectorAll('[data-case]').forEach(function (a) {
      a.addEventListener('click', function (e) {
        e.preventDefault();
        lastTrigger = a;
        open(a.dataset.case);
      });
    });

    // deep link: projects.html#case-night-shift
    var hash = window.location.hash.slice(1);
    var target = hash && document.getElementById(hash);
    if (target && target.matches('dialog.case')) {
      lastTrigger = document.querySelector('[data-case="' + hash + '"]');
      open(hash);
    }
  }

  /* ----------------------------------------------------------------
   * Availability calendar: current month + the next two, built from
   * the data-booked / data-hold day ranges (month offset: days).
   * ---------------------------------------------------------------- */
  function initCalendar() {
    var root = document.querySelector('[data-calendar]');
    if (!root) return;

    function parse(str) {
      var map = {};
      (str || '').split(';').forEach(function (part) {
        var bits = part.split(':');
        if (bits.length < 2) return;
        var days = map[+bits[0]] = map[+bits[0]] || {};
        bits[1].split(',').forEach(function (range) {
          var r = range.split('-').map(Number);
          for (var d = r[0]; d <= (r[1] || r[0]); d++) days[d] = true;
        });
      });
      return map;
    }

    var booked = parse(root.dataset.booked);
    var hold = parse(root.dataset.hold);
    var today = new Date(); today.setHours(0, 0, 0, 0);
    var monthFmt = new Intl.DateTimeFormat('en-US', { month: 'long', year: 'numeric' });
    var dayFmt = new Intl.DateTimeFormat('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
    var shortFmt = new Intl.DateTimeFormat('en-US', { month: 'short', day: 'numeric' });
    var weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    var wrap = document.createElement('div');
    wrap.className = 'cal-months';
    var firstOpen = null;

    for (var m = 0; m < 3; m++) {
      var first = new Date(today.getFullYear(), today.getMonth() + m, 1);
      var total = new Date(first.getFullYear(), first.getMonth() + 1, 0).getDate();
      var lead = (first.getDay() + 6) % 7;
      var open = 0;
      var titleId = 'cal-m' + m;
      var html = '<table class="cal-table" aria-labelledby="' + titleId + '"><thead><tr>' +
        weekdays.map(function (w) { return '<th scope="col" abbr="' + w + '">' + w.charAt(0) + '</th>'; }).join('') +
        '</tr></thead><tbody><tr>';
      for (var i = 0; i < lead; i++) html += '<td></td>';
      for (var d = 1; d <= total; d++) {
        var date = new Date(first.getFullYear(), first.getMonth(), d);
        var dow = date.getDay();
        var label = dayFmt.format(date);
        var cell;
        if (date < today) {
          cell = '<span class="day is-past">' + d + '<span class="visually-hidden">, ' + label + ', past</span></span>';
        } else if (dow === 0 || dow === 6) {
          cell = '<span class="day is-past">' + d + '<span class="visually-hidden">, ' + label + ', studio closed</span></span>';
        } else if (booked[m] && booked[m][d]) {
          cell = '<span class="day is-booked">' + d + '<span class="visually-hidden">, ' + label + ', booked</span></span>';
        } else if (hold[m] && hold[m][d]) {
          cell = '<span class="day is-hold">' + d + '<span class="visually-hidden">, ' + label + ', pencilled in</span></span>';
        } else {
          open++;
          if (!firstOpen) firstOpen = date;
          cell = '<button type="button" class="day is-open" data-date="' + isoDate(date) + '" aria-pressed="false" aria-label="' + label + ', open. Set as preferred start">' + d + '</button>';
        }
        html += '<td>' + cell + '</td>';
        if ((lead + d) % 7 === 0 && d !== total) html += '</tr><tr>';
      }
      var trailing = (7 - ((lead + total) % 7)) % 7;
      for (var t = 0; t < trailing; t++) html += '<td></td>';
      html += '</tr></tbody></table>';

      var month = document.createElement('div');
      month.className = 'cal-month';
      month.innerHTML = '<div class="cal-head"><h3 id="' + titleId + '">' + monthFmt.format(first) + '</h3><span>' +
        (open ? open + ' open day' + (open === 1 ? '' : 's') : 'Fully booked') + '</span></div>' + html;
      wrap.appendChild(month);
    }

    root.replaceChildren(wrap);

    var nextOpen = document.querySelector('[data-next-open]');
    if (nextOpen && firstOpen) nextOpen.textContent = shortFmt.format(firstOpen);

    var note = document.querySelector('.cal-note');
    var startInput = document.getElementById('c-start');
    wrap.addEventListener('click', function (e) {
      var btn = e.target.closest('.day.is-open');
      if (!btn) return;
      wrap.querySelectorAll('.day[aria-pressed="true"]').forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
      btn.setAttribute('aria-pressed', 'true');
      var picked = new Date(btn.dataset.date + 'T00:00:00');
      if (startInput) startInput.value = btn.dataset.date;
      if (note) note.textContent = 'Preferred start set to ' + dayFmt.format(picked) + '. It is filled in on the brief form below.';
    });
  }

  /* ----------------------------------------------------------------
   * Commission brief: validation, type prefill, counter, success.
   * ---------------------------------------------------------------- */
  function initCommissionForm() {
    var form = document.querySelector('[data-commission]');
    if (!form) return;
    var today = isoDate(new Date());
    var deadline = form.querySelector('#c-deadline');
    var start = form.querySelector('#c-start');
    if (deadline) deadline.min = today;
    if (start) start.min = today;

    var type = new URLSearchParams(window.location.search).get('type');
    if (type) {
      var radio = form.querySelector('input[name="type"][value="' + CSS.escape(type) + '"]');
      if (radio) radio.checked = true;
    }

    var brief = form.querySelector('#c-brief');
    var counter = form.querySelector('[data-count-for="c-brief"]');
    function count() { if (brief && counter) counter.textContent = brief.value.length + ' / ' + brief.maxLength; }
    if (brief) brief.addEventListener('input', count);
    count();

    var rules = [
      ['#c-name', function (el) { return el.value.trim().length > 1; }],
      ['#c-email', function (el) { return EMAIL_RE.test(el.value.trim()); }],
      ['#c-usage', function (el) { return el.value !== ''; }],
      ['#c-deadline', function (el) { return !!el.value && el.value > today; }],
      ['#c-brief', function (el) { return el.value.trim().length >= 30; }],
      ['#c-agree', function (el) { return el.checked; }],
    ];
    var groups = ['type', 'budget'];

    function mark(wrap, ok, el) {
      if (!wrap) return;
      wrap.classList.toggle('is-invalid', !ok);
      (el ? [el] : wrap.querySelectorAll('input')).forEach(function (x) { x.setAttribute('aria-invalid', String(!ok)); });
    }

    function validate() {
      var invalid = [];
      rules.forEach(function (r) {
        var el = form.querySelector(r[0]);
        if (!el) return;
        var ok = r[1](el);
        mark(el.closest('.field'), ok, el);
        if (!ok) invalid.push(el);
      });
      groups.forEach(function (g) {
        var wrap = form.querySelector('[data-group="' + g + '"]');
        if (!wrap) return;
        var ok = !!form.querySelector('input[name="' + g + '"]:checked');
        mark(wrap, ok);
        if (!ok) invalid.push(wrap.querySelector('input'));
      });
      invalid.sort(function (a, b) { return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1; });
      return invalid[0] || null;
    }

    // once a field has been flagged, re-check it as the visitor fixes it
    form.addEventListener('input', function (e) { if (e.target.closest('.is-invalid')) validate(); });
    form.addEventListener('change', function (e) { if (e.target.closest('.is-invalid')) validate(); });

    var success = form.querySelector('.form-success');
    var successText = form.querySelector('[data-success-text]');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var first = validate();
      if (first) { first.focus(); return; }
      var name = form.querySelector('#c-name').value.trim().split(/\s+/)[0];
      if (successText) successText.textContent = 'Thanks, ' + name + '. I read every brief myself and reply within two working days with a fixed quote and a timeline.';
      form.classList.add('is-sent');
      if (success) success.focus();
    });

    var again = form.querySelector('[data-reset]');
    if (again) {
      again.addEventListener('click', function () {
        form.reset();
        form.classList.remove('is-sent');
        form.querySelectorAll('.is-invalid').forEach(function (x) { x.classList.remove('is-invalid'); });
        count();
        form.querySelector('#c-name').focus();
      });
    }
  }

  /* ----------------------------------------------------------------
   * Reference upload: drag and drop, previews, remove, limits.
   * Files stay in the browser; connect the form to a service to send.
   * ---------------------------------------------------------------- */
  function initUploads() {
    var zone = document.querySelector('[data-dropzone]');
    if (!zone) return;
    var input = zone.querySelector('input[type="file"]');
    var list = zone.querySelector('.file-list');
    var msg = zone.querySelector('.upload-msg');
    if (!input || !list) return;
    var MAX = 6;
    var MAX_MB = 10;
    var files = [];

    function okType(f) { return /^image\/(jpeg|png|webp)$/.test(f.type) || f.type === 'application/pdf'; }
    function size(b) { return b > 1048576 ? (b / 1048576).toFixed(1) + ' MB' : Math.max(1, Math.round(b / 1024)) + ' KB'; }

    function render() {
      list.querySelectorAll('img').forEach(function (img) { URL.revokeObjectURL(img.src); });
      list.replaceChildren();
      files.forEach(function (f, i) {
        var li = document.createElement('li');
        li.className = 'file-item';
        var thumb = document.createElement('span');
        thumb.className = 'file-thumb';
        if (f.type.indexOf('image/') === 0) {
          var img = document.createElement('img');
          img.src = URL.createObjectURL(f);
          img.alt = '';
          thumb.appendChild(img);
        } else {
          thumb.textContent = 'PDF';
        }
        var info = document.createElement('span');
        info.className = 'file-info';
        var name = document.createElement('b');
        name.textContent = f.name;
        var meta = document.createElement('span');
        meta.textContent = size(f.size) + ' · ' + (f.type === 'application/pdf' ? 'PDF' : 'image');
        info.append(name, meta);
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'file-remove';
        btn.dataset.remove = String(i);
        btn.setAttribute('aria-label', 'Remove ' + f.name);
        btn.innerHTML = ICON_X;
        li.append(thumb, info, btn);
        list.appendChild(li);
      });
    }

    function sync() {
      if (window.DataTransfer) {
        try {
          var dt = new DataTransfer();
          files.forEach(function (f) { dt.items.add(f); });
          input.files = dt.files;
        } catch (err) { /* older browsers keep the last selection */ }
      }
      render();
    }

    function add(incoming) {
      var skipped = [];
      Array.prototype.forEach.call(incoming, function (f) {
        if (files.some(function (x) { return x.name === f.name && x.size === f.size; })) return;
        if (files.length >= MAX) skipped.push(f.name + ' (limit is ' + MAX + ' files)');
        else if (!okType(f)) skipped.push(f.name + ' (use JPG, PNG, WebP or PDF)');
        else if (f.size > MAX_MB * 1048576) skipped.push(f.name + ' (over ' + MAX_MB + ' MB)');
        else files.push(f);
      });
      if (msg) {
        msg.textContent = skipped.length ? 'Skipped ' + skipped.join(', ') + '.' : files.length + ' reference' + (files.length === 1 ? '' : 's') + ' attached.';
        msg.classList.toggle('is-error', skipped.length > 0);
      }
      sync();
    }

    input.addEventListener('change', function () { if (input.files.length) add(input.files); });
    ['dragenter', 'dragover'].forEach(function (ev) {
      zone.addEventListener(ev, function (e) { e.preventDefault(); zone.classList.add('is-over'); });
    });
    zone.addEventListener('dragleave', function (e) { if (!zone.contains(e.relatedTarget)) zone.classList.remove('is-over'); });
    zone.addEventListener('drop', function (e) {
      e.preventDefault();
      zone.classList.remove('is-over');
      if (e.dataTransfer && e.dataTransfer.files.length) add(e.dataTransfer.files);
    });
    list.addEventListener('click', function (e) {
      var btn = e.target.closest('[data-remove]');
      if (!btn) return;
      var removed = files.splice(+btn.dataset.remove, 1)[0];
      if (msg) { msg.textContent = 'Removed ' + removed.name + '.'; msg.classList.remove('is-error'); }
      sync();
      var next = list.querySelector('[data-remove]');
      (next || input).focus();
    });
    var form = zone.closest('form');
    if (form) form.addEventListener('reset', function () { files = []; sync(); if (msg) msg.textContent = ''; });
  }

  /* ----------------------------------------------------------------
   * Shop strip: add or remove items from a demo bag.
   * ---------------------------------------------------------------- */
  function initShop() {
    var buttons = document.querySelectorAll('.add-bag');
    var text = document.querySelector('[data-bag-text]');
    if (!buttons.length || !text) return;
    var bag = {};
    function render() {
      var names = Object.keys(bag);
      var total = names.reduce(function (sum, k) { return sum + bag[k]; }, 0);
      text.textContent = names.length
        ? names.length + ' item' + (names.length === 1 ? '' : 's') + ' in your bag · $' + total
        : 'Your bag is empty';
    }
    buttons.forEach(function (b) {
      b.addEventListener('click', function () {
        var on = b.getAttribute('aria-pressed') !== 'true';
        b.setAttribute('aria-pressed', String(on));
        b.innerHTML = (on ? ICON_CHECK : ICON_PLUS) + ' <span>' + (on ? 'Added' : 'Add to bag') + '</span>';
        if (on) bag[b.dataset.product] = +b.dataset.price; else delete bag[b.dataset.product];
        render();
      });
    });
  }

  /* ----------------------------------------------------------------
   * Footer newsletter: validate, then confirm.
   * ---------------------------------------------------------------- */
  function initNewsletter() {
    document.querySelectorAll('[data-newsletter]').forEach(function (form) {
      var input = form.querySelector('input[type="email"]');
      var msg = form.parentElement.querySelector('.news-msg');
      if (!input || !msg) return;
      form.addEventListener('submit', function (e) {
        e.preventDefault();
        var ok = EMAIL_RE.test(input.value.trim());
        input.setAttribute('aria-invalid', String(!ok));
        msg.classList.toggle('is-error', !ok);
        msg.classList.toggle('is-ok', ok);
        msg.textContent = ok ? "Thanks, you're on the list for the next letter." : 'Please enter a valid email address.';
        if (ok) form.reset(); else input.focus();
      });
    });
  }

  function init() {
    initNav();
    initHeaderScroll();
    initReveal();
    initMarquee();
    initYear();
    initProjectFilters();
    initCaseDialogs();
    initCalendar();
    initCommissionForm();
    initUploads();
    initShop();
    initNewsletter();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
