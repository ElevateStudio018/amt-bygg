/* AMT Bygg – gränssnitt */
(function () {
  'use strict';
  var doc = document.documentElement;
  var body = document.body;
  doc.classList.remove('no-js');

  /* Megameny: öppnas vid hovring och med tangentbord */
  document.querySelectorAll('.nav__item--drop').forEach(function (item) {
    var link = item.querySelector('.nav__link');
    var timer;
    function open() { clearTimeout(timer); item.classList.add('is-open'); link.setAttribute('aria-expanded', 'true'); }
    function close() { item.classList.remove('is-open'); link.setAttribute('aria-expanded', 'false'); }
    item.addEventListener('mouseenter', open);
    item.addEventListener('mouseleave', function () { timer = setTimeout(close, 120); });
    item.addEventListener('focusout', function (e) { if (!item.contains(e.relatedTarget)) close(); });
    item.addEventListener('keydown', function (e) { if (e.key === 'Escape') { close(); link.focus(); } });
    link.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') { e.preventDefault(); open(); var a = item.querySelector('.mega a'); if (a) a.focus(); }
    });
    link.addEventListener('click', function (e) {
      if (!window.matchMedia('(hover: hover)').matches && !item.classList.contains('is-open')) { e.preventDefault(); open(); }
    });
  });

  /* Mobilmeny */
  var toggle = document.querySelector('.menu-toggle');
  var mobile = document.getElementById('mobile-nav');
  var header = document.querySelector('.header');
  function setOpen(open) {
    if (open) doc.style.setProperty('--mn-top', Math.round(header.getBoundingClientRect().bottom) + 'px');
    body.classList.toggle('menu-open', open);
    mobile.hidden = !open;
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Stäng meny' : 'Öppna meny');
  }
  if (toggle && mobile) {
    toggle.addEventListener('click', function () { setOpen(!body.classList.contains('menu-open')); });
    mobile.addEventListener('click', function (e) { if (e.target.closest('a')) setOpen(false); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && body.classList.contains('menu-open')) setOpen(false); });
    window.addEventListener('resize', function () { if (window.innerWidth > 1180 && body.classList.contains('menu-open')) setOpen(false); });
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
        var btn = form.querySelector('[type="submit"]');
        if (btn) btn.disabled = true;
        fetch(endpoint, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' } })
          .then(function (r) { if (!r.ok) throw new Error(r.status); form.reset(); show(form.getAttribute('data-success')); })
          .catch(function () { show('Meddelandet kunde inte skickas. Ring oss på 031-45 40 45 eller mejla ' + to + '.'); })
          .finally(function () { if (btn) btn.disabled = false; });
        return;
      }
      var subject = form.getAttribute('data-subject') || 'Förfrågan via amtgroup.se';
      var lines = [];
      form.querySelectorAll('[name]').forEach(function (el) {
        if (el.type === 'file' || el.type === 'checkbox' || !el.value) return;
        var label = form.querySelector('label[for="' + el.id + '"]');
        lines.push((label ? label.textContent.replace('*', '').trim() : el.name) + ': ' + el.value);
        if (el.name === 'amne') subject += ' – ' + el.value;
        if (el.name === 'skadenummer') subject += ' – skadenr ' + el.value;
      });
      var file = form.querySelector('input[type="file"]');
      if (file && file.files.length) lines.push('', '(Bifoga filen ' + file.files[0].name + ' i det här mejlet innan du skickar.)');
      window.location.href = 'mailto:' + to + '?subject=' + encodeURIComponent(subject) + '&body=' + encodeURIComponent(lines.join('\n'));
      show(form.getAttribute('data-mailto-note'));
    });
  });

  /* Filnamn i filväljaren */
  document.querySelectorAll('input[data-file]').forEach(function (inp) {
    var out = inp.parentElement.querySelector('[data-file-name]');
    inp.addEventListener('change', function () { out.textContent = inp.files.length ? inp.files[0].name : 'Ingen fil vald'; });
  });

  var y = document.querySelector('[data-year]');
  if (y) y.textContent = new Date().getFullYear();
})();
