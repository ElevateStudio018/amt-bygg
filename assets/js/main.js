/* AMT Bygg – gränssnitt */
(function () {
  'use strict';
  var doc = document.documentElement;
  var body = document.body;
  doc.classList.remove('no-js');

  /* Header: tillstånd vid scroll */
  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    body.classList.toggle('is-scrolled', y > 24);
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Megameny */
  var dropItems = document.querySelectorAll('.nav__item--drop');
  dropItems.forEach(function (item) {
    var btn = item.querySelector('[aria-expanded]');
    var closeTimer;
    function open() { clearTimeout(closeTimer); item.classList.add('is-open'); btn.setAttribute('aria-expanded', 'true'); }
    function close() { item.classList.remove('is-open'); btn.setAttribute('aria-expanded', 'false'); }
    item.addEventListener('mouseenter', open);
    item.addEventListener('mouseleave', function () { closeTimer = setTimeout(close, 140); });
    btn.addEventListener('click', function (e) {
      if (window.matchMedia('(hover: hover)').matches && btn.tagName === 'A') return;
      e.preventDefault();
      item.classList.contains('is-open') ? close() : open();
    });
    item.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') { close(); btn.focus(); }
    });
    item.addEventListener('focusout', function (e) {
      if (!item.contains(e.relatedTarget)) close();
    });
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); open(); var f = item.querySelector('.mega a'); if (f) f.focus(); }
    });
  });

  /* Mobilmeny */
  var toggle = document.querySelector('.menu-toggle');
  var mobile = document.getElementById('mobile-nav');
  if (toggle && mobile) {
    toggle.addEventListener('click', function () {
      var open = !body.classList.contains('menu-open');
      body.classList.toggle('menu-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      toggle.setAttribute('aria-label', open ? 'Stäng meny' : 'Öppna meny');
      mobile.toggleAttribute('inert', !open);
      mobile.setAttribute('aria-hidden', String(!open));
    });
    mobile.addEventListener('click', function (e) {
      if (e.target.closest('a')) { body.classList.remove('menu-open'); toggle.setAttribute('aria-expanded', 'false'); mobile.setAttribute('inert', ''); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && body.classList.contains('menu-open')) toggle.click();
    });
  }

  /* Visa vid scroll */
  var reveals = document.querySelectorAll('.reveal, .process');
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-visible'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: .08 });
    reveals.forEach(function (el) { io.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-visible'); });
  }

  /* Diskret parallax på helbreddsbilder */
  var bleeds = document.querySelectorAll('.bleed img');
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if (bleeds.length && !reduce) {
    var ticking = false;
    function para() {
      bleeds.forEach(function (img) {
        var r = img.parentElement.getBoundingClientRect();
        var vh = window.innerHeight;
        if (r.bottom < 0 || r.top > vh) return;
        var p = (r.top + r.height / 2 - vh / 2) / vh;
        img.style.transform = 'translate3d(0,' + (p * -9 - 6).toFixed(2) + '%,0)';
      });
      ticking = false;
    }
    window.addEventListener('scroll', function () { if (!ticking) { requestAnimationFrame(para); ticking = true; } }, { passive: true });
    para();
  }

  /* Formulär
     Om formuläret har data-endpoint skickas det dit (t.ex. Formspree eller egen backend).
     Annars öppnas ett förifyllt mejl till mottagaren. */
  document.querySelectorAll('form[data-form]').forEach(function (form) {
    var status = form.querySelector('.form__status');
    function show(msg) { if (status) { status.textContent = msg; status.classList.add('is-shown'); status.focus && status.focus(); } }
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) return;
      e.preventDefault();
      var endpoint = form.getAttribute('data-endpoint');
      var to = form.getAttribute('data-mailto');
      var subjectPrefix = form.getAttribute('data-subject') || 'Förfrågan via amtgroup.se';
      var data = new FormData(form);
      if (endpoint) {
        var btn = form.querySelector('[type="submit"]');
        if (btn) btn.disabled = true;
        fetch(endpoint, { method: 'POST', body: data, headers: { 'Accept': 'application/json' } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); form.reset(); show(form.getAttribute('data-success')); })
          .catch(function () { show('Något gick fel. Ring oss gärna på 031-45 40 45 eller mejla ' + to + '.'); })
          .finally(function () { if (btn) btn.disabled = false; });
        return;
      }
      var lines = [];
      var subject = subjectPrefix;
      form.querySelectorAll('[name]').forEach(function (el) {
        if (el.type === 'file' || el.type === 'checkbox' || el.type === 'hidden') return;
        var label = form.querySelector('label[for="' + el.id + '"]');
        var name = label ? label.textContent.replace('*', '').trim() : el.name;
        if (el.name === 'amne' && el.value) subject = subjectPrefix + ' – ' + el.value;
        if (el.name === 'skadenummer' && el.value) subject = subjectPrefix + ' – skadenr ' + el.value;
        if (el.value) lines.push(name + ': ' + el.value);
      });
      var hasFile = form.querySelector('input[type="file"]') && form.querySelector('input[type="file"]').files.length;
      if (hasFile) lines.push('', '(Bifoga filen från försäkringsbolaget i det här mejlet innan du skickar.)');
      window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
      show(form.getAttribute('data-mailto-note'));
    });
  });

  /* Filnamn i filväljaren */
  document.querySelectorAll('input[data-file]').forEach(function (inp) {
    var out = inp.parentElement.querySelector('[data-file-name]');
    inp.addEventListener('change', function () {
      out.textContent = inp.files.length ? inp.files[0].name : 'Ingen fil vald';
    });
  });

  /* Årtal i sidfot */
  var y = document.querySelector('[data-year]');
  if (y) y.textContent = new Date().getFullYear();
})();
