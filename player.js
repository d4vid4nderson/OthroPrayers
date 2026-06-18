/* Read-aloud for the prayers, using the browser's built-in speech synthesis.
 * A small play button is added to each prayer; a floating mini-player offers
 * pause/resume, previous, next and stop, and the prayer being read is
 * highlighted. No audio files or network are needed. */
(function () {
  if (!('speechSynthesis' in window)) return;
  var synth = window.speechSynthesis;
  // the prayer body paragraphs + centred couplets (skip rubrics/instructions)
  var items = [].slice.call(document.querySelectorAll('main.book > p:not(.rubric)'));
  if (!items.length) return;

  var ICON = {
    play:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>',
    prev:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 6h2v12H7zm3 6l9 6V6z"/></svg>',
    next:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6h2v12h-2zM5 6l9 6-9 6z"/></svg>',
    stop:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6h12v12H6z"/></svg>'
  };

  // spoken-only pronunciation nudges for liturgical words
  var FIX = [
    [/\bTheotokos\b/gi, 'Theh-oh-toh-koss'],
    [/\bTrisagion\b/gi, 'Tri-sah-ghee-on'],
    [/\bcherubim\b/gi, 'chair-oo-bim'],
    [/\bseraphim\b/gi, 'sair-uh-fim'],
    [/\bhomoousios\b/gi, 'ho-mo-oo-see-os']
  ];
  function textOf(el) {
    var t = el.textContent.replace(/[℟✠❧]/g, ' ')  /* ℟ ✠ ❧ */
                          .replace(/­/g, '').replace(/\s+/g, ' ').trim();
    for (var i = 0; i < FIX.length; i++) t = t.replace(FIX[i][0], FIX[i][1]);
    return t;
  }

  var voice = null;
  function pickVoice() {
    var vs = synth.getVoices().filter(function (v) { return /^en/i.test(v.lang); });
    var pref = ['Google US English', 'Samantha', 'Microsoft Aria', 'Microsoft Jenny',
                'Daniel', 'Karen', 'Moira', 'Google UK English Female'];
    for (var i = 0; i < pref.length; i++)
      for (var j = 0; j < vs.length; j++)
        if (vs[j].name.indexOf(pref[i]) >= 0) { voice = vs[j]; return; }
    voice = vs[0] || null;
  }
  pickVoice();
  if (typeof synth.onvoiceschanged !== 'undefined') synth.addEventListener('voiceschanged', pickVoice);

  var cur = -1, gen = 0, paused = false, active = false;

  // per-prayer play buttons
  items.forEach(function (el, idx) {
    el.classList.add('sayable');
    var b = document.createElement('button');
    b.className = 'say-btn'; b.type = 'button';
    b.setAttribute('aria-label', 'Read this prayer aloud');
    b.innerHTML = ICON.play;
    b.addEventListener('click', function (e) { e.stopPropagation(); startAt(idx); });
    el.insertBefore(b, el.firstChild);
    // while reading, tap a prayer to skip the audio to it
    el.addEventListener('click', function (e) {
      if (!active || e.target.closest('.say-btn')) return;
      if (window.getSelection && String(window.getSelection()).trim()) return; // keep text selection
      startAt(idx);
    });
  });

  // floating mini-player
  var bar = document.createElement('div');
  bar.className = 'ttsbar'; bar.setAttribute('role', 'toolbar');
  bar.setAttribute('aria-label', 'Read aloud controls'); bar.hidden = true;
  function btn(act, label, icon) {
    return '<button type="button" data-act="' + act + '" aria-label="' + label + '">' + icon + '</button>';
  }
  bar.innerHTML = btn('prev', 'Previous prayer', ICON.prev) +
                  btn('toggle', 'Pause', ICON.pause) +
                  btn('next', 'Next prayer', ICON.next) +
                  btn('stop', 'Stop', ICON.stop);
  document.body.appendChild(bar);
  var toggleBtn = bar.querySelector('[data-act=toggle]');

  function highlight() {
    items.forEach(function (el) { el.classList.remove('speaking'); });
    if (cur >= 0 && cur < items.length) {
      var el = items[cur]; el.classList.add('speaking');
      var r = el.getBoundingClientRect();
      if (r.top < 70 || r.bottom > window.innerHeight - 150)
        el.scrollIntoView({ block: 'center', behavior: 'smooth' });
    }
  }
  function setPaused(p) {
    paused = p;
    toggleBtn.innerHTML = p ? ICON.play : ICON.pause;
    toggleBtn.setAttribute('aria-label', p ? 'Resume' : 'Pause');
  }

  function speakCur() {
    if (cur < 0 || cur >= items.length) { stop(); return; }
    highlight();
    var g = gen;
    var u = new SpeechSynthesisUtterance(textOf(items[cur]));
    if (voice) u.voice = voice;
    u.rate = 0.95; u.pitch = 1;
    u.onend = function () { if (g !== gen) return; cur++; if (cur < items.length) speakCur(); else stop(); };
    u.onerror = function () { if (g !== gen) return; cur++; if (cur < items.length) speakCur(); else stop(); };
    synth.speak(u);
  }
  function startAt(idx) { gen++; synth.cancel(); cur = idx; active = true; setPaused(false); bar.hidden = false; document.documentElement.classList.add('tts-on'); setTimeout(speakCur, 60); }
  function stop() { gen++; active = false; setPaused(false); synth.cancel(); items.forEach(function (el) { el.classList.remove('speaking'); }); bar.hidden = true; document.documentElement.classList.remove('tts-on'); }
  function next() { if (!active) return; gen++; synth.cancel(); cur++; setPaused(false); if (cur < items.length) setTimeout(speakCur, 60); else stop(); }
  function prev() { if (!active) return; gen++; synth.cancel(); cur = Math.max(0, cur - 1); setPaused(false); setTimeout(speakCur, 60); }
  function toggle() {
    if (!active) return;
    if (paused) { setPaused(false); try { synth.resume(); } catch (e) {} }
    else { setPaused(true); try { synth.pause(); } catch (e) {} }
  }

  bar.addEventListener('click', function (e) {
    var b = e.target.closest('button'); if (!b) return;
    var a = b.getAttribute('data-act');
    if (a === 'toggle') toggle(); else if (a === 'next') next();
    else if (a === 'prev') prev(); else if (a === 'stop') stop();
  });
  window.addEventListener('pagehide', function () { try { synth.cancel(); } catch (e) {} });
})();
