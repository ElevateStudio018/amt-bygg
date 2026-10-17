/* AMT Bygg – gränssnitt */
(function () {
  'use strict';
  var doc = document.documentElement;
  var body = document.body;
  var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* Header: blir solid vid scroll och göms när man scrollar nedåt */
  var lastY = 0;
  function onScroll() {
    var y = window.scrollY || window.pageYOffset;
    body.classList.toggle('is-scrolled', y > 40);
    if (!body.classList.contains('menu-open')) body.classList.toggle('is-hidden', y > 400 && y > lastY + 4);
    if (y < lastY - 4) body.classList.remove('is-hidden');
    lastY = y;
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  /* Helskärmsmeny */
  var btn = document.querySelector('.menu-btn');
  var menu = document.getElementById('menu');
  var label = btn && btn.querySelector('[data-menu-label]');
  function setMenu(open) {
    body.classList.toggle('menu-open', open);
    body.classList.remove('is-hidden');
    btn.setAttribute('aria-expanded', String(open));
    label.textContent = open ? 'Stäng' : 'Meny';
    if (open) { menu.hidden = false; requestAnimationFrame(function () { var a = menu.querySelector('a'); if (a) a.focus(); }); }
    else { setTimeout(function () { if (!body.classList.contains('menu-open')) menu.hidden = true; }, 400); btn.focus(); }
  }
  if (btn && menu) {
    btn.addEventListener('click', function () { setMenu(!body.classList.contains('menu-open')); });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && body.classList.contains('menu-open')) setMenu(false);
      if (e.key === 'Tab' && body.classList.contains('menu-open')) {
        var f = [btn].concat([].slice.call(menu.querySelectorAll('a')));
        var i = f.indexOf(document.activeElement);
        if (e.shiftKey && i <= 0) { e.preventDefault(); f[f.length - 1].focus(); }
        else if (!e.shiftKey && i === f.length - 1) { e.preventDefault(); f[0].focus(); }
      }
    });
    menu.addEventListener('click', function (e) { if (e.target.closest('a')) body.classList.remove('menu-open'); });
  }

  /* Affärsområden: byt bild när respektive text kommer in i bild */
  var stickImgs = document.querySelectorAll('[data-stick]');
  if (stickImgs.length && 'IntersectionObserver' in window) {
    var so = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        var i = en.target.getAttribute('data-stick-panel');
        stickImgs.forEach(function (p) { p.classList.toggle('is-active', p.getAttribute('data-stick') === i); });
      });
    }, { rootMargin: '-45% 0px -45% 0px' });
    document.querySelectorAll('[data-stick-panel]').forEach(function (p) { so.observe(p); });
  }

  /* Karusell */
  document.querySelectorAll('[data-rail]').forEach(function (rail) {
    var scope = rail.closest('section') || document;
    var prev = scope.querySelector('[data-rail-prev]');
    var next = scope.querySelector('[data-rail-next]');
    function step() { var c = rail.firstElementChild; return c ? c.getBoundingClientRect().width + 24 : 300; }
    function update() {
      if (!prev) return;
      prev.disabled = rail.scrollLeft < 8;
      next.disabled = rail.scrollLeft + rail.clientWidth > rail.scrollWidth - 8;
    }
    if (prev) prev.addEventListener('click', function () { rail.scrollBy({ left: -step(), behavior: reduce ? 'auto' : 'smooth' }); });
    if (next) next.addEventListener('click', function () { rail.scrollBy({ left: step(), behavior: reduce ? 'auto' : 'smooth' }); });
    rail.addEventListener('scroll', update, { passive: true });
    window.addEventListener('resize', update);
    update();
  });

  /* Mjuk inglidning för sektioner */
  var reveals = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && !reduce) {
    var ro = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) { if (en.isIntersecting) { en.target.classList.add('is-in'); ro.unobserve(en.target); } });
    }, { rootMargin: '0px 0px -6% 0px' });
    reveals.forEach(function (el) { ro.observe(el); });
  } else {
    reveals.forEach(function (el) { el.classList.add('is-in'); });
  }

  /* Formulär
     Med data-endpoint skickas formuläret dit (t.ex. Formspree).
     Annars öppnas ett förifyllt mejl till mottagaren. */
  document.querySelectorAll('form[data-form]').forEach(function (form) {
    var status = form.querySelector('.form__status');
    function show(msg) { if (status) { status.textContent = msg; status.classList.add('is-shown'); status.focus(); } }
    form.addEventListener('submit', function (e) {
      if (!form.checkValidity()) return;
      e.preventDefault();
      var endpoint = form.getAttribute('data-endpoint');
      var to = form.getAttribute('data-mailto');
      if (endpoint) {
        var sb = form.querySelector('[type="submit"]');
        if (sb) sb.disabled = true;
        fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); form.reset(); show(form.getAttribute('data-success')); })
          .catch(function () { show('Meddelandet kunde inte skickas. Ring oss på 031-45 40 45 eller mejla ' + to + '.'); })
          .finally(function () { if (sb) sb.disabled = false; });
        return;
      }
      var subject = form.getAttribute('data-subject') || 'Förfrågan via amtgroup.se';
      var lines = [];
      form.querySelectorAll('[name]').forEach(function (el) {
        if (el.type === 'file' || el.type === 'checkbox' || !el.value) return;
        var l = form.querySelector('label[for="' + el.id + '"]');
        lines.push((l ? l.textContent.replace('*', '').trim() : el.name) + ': ' + el.value);
        if (el.name === 'amne') subject += ' – ' + el.value;
        if (el.name === 'skadenummer') subject += ' – skadenr ' + el.value;
      });
      var file = form.querySelector('input[type="file"]');
      if (file && file.files.length) lines.push('', '(Bifoga filen ' + file.files[0].name + ' i det här mejlet innan du skickar.)');
      window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
      show(form.getAttribute('data-mailto-note'));
    });
  });

  document.querySelectorAll('input[data-file]').forEach(function (inp) {
    var out = inp.parentElement.querySelector('[data-file-name]');
    inp.addEventListener('change', function () { out.textContent = inp.files.length ? inp.files[0].name : 'Ingen fil vald'; });
  });

  var yr = document.querySelector('[data-year]');
  if (yr) yr.textContent = new Date().getFullYear();
})();
