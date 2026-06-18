/* Read-aloud for the prayers, using the browser's built-in speech synthesis.
 * The reader is started ONLY by the floating "Listen" button. Once it's
 * running, tapping a prayer skips the audio to it; a mini-player offers
 * pause/resume, previous, next, stop, and a playback-speed control. Tapping
 * text does nothing while the reader is inactive (so scrolling never starts
 * it). No audio files or network needed. */
(function () {
  if (!('speechSynthesis' in window)) return;
  var synth = window.speechSynthesis;
  var items = [].slice.call(document.querySelectorAll('main.book > p:not(.rubric)'));
  if (!items.length) return;

  var ICON = {
    play:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 5v14l11-7z"/></svg>',
    pause: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 5h4v14H6zM14 5h4v14h-4z"/></svg>',
    prev:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 6h2v12H7zm3 6l9 6V6z"/></svg>',
    next:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 6h2v12h-2zM5 6l9 6-9 6z"/></svg>',
    stop:  '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6h12v12H6z"/></svg>'
  };

  var FIX = [
    [/\bTheotokos\b/gi, 'Theh-oh-toh-koss'],
    [/\bTrisagion\b/gi, 'Tri-sah-ghee-on'],
    [/\bcherubim\b/gi, 'chair-oo-bim'],
    [/\bseraphim\b/gi, 'sair-uh-fim'],
    [/\bhomoousios\b/gi, 'ho-mo-oo-see-os']
  ];
  function textOf(el) {
    var t = el.textContent.replace(/[℟✠❧]/g, ' ')
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

  // playback speed (persisted)
  var SPEEDS = [0.75, 1, 1.25, 1.5, 2];
  var rate = parseFloat(localStorage.getItem('ttsrate'));
  var si = SPEEDS.indexOf(rate);
  if (si < 0) { rate = 1; si = SPEEDS.indexOf(1); }
  function speedLabel() { return (String(rate).replace(/\.0$/, '')) + '×'; }

  // mark prayers; tapping one skips the audio there — but ONLY while reading
  items.forEach(function (el, idx) {
    el.classList.add('sayable');
    el.addEventListener('click', function (e) {
      if (!active) return;                                   // inactive: ignore taps (scrolling is safe)
      if (window.getSelection && String(window.getSelection()).trim()) return; // keep text selection
      startAt(idx);
    });
  });

  // the ONLY way to start: a floating "Listen" button
  var fab = document.createElement('button');
  fab.className = 'tts-fab'; fab.type = 'button';
  fab.setAttribute('aria-label', 'Listen to the prayers');
  fab.innerHTML = ICON.play + '<span>Listen</span>';
  fab.addEventListener('click', startFromView);
  document.body.appendChild(fab);

  // mini-player (shown only while reading)
  var bar = document.createElement('div');
  bar.className = 'ttsbar'; bar.setAttribute('role', 'toolbar');
  bar.setAttribute('aria-label', 'Read aloud controls'); bar.hidden = true;
  function btn(act, label, icon) {
    return '<button type="button" data-act="' + act + '" aria-label="' + label + '">' + icon + '</button>';
  }
  bar.innerHTML = btn('prev', 'Previous prayer', ICON.prev) +
                  btn('toggle', 'Pause', ICON.pause) +
                  btn('next', 'Next prayer', ICON.next) +
                  btn('stop', 'Stop', ICON.stop) +
                  '<button type="button" class="tts-speed" data-act="speed" aria-label="Playback speed"></button>';
  document.body.appendChild(bar);
  var toggleBtn = bar.querySelector('[data-act=toggle]');
  var speedBtn = bar.querySelector('[data-act=speed]');
  speedBtn.textContent = speedLabel();
  function cycleSpeed() {
    si = (si + 1) % SPEEDS.length; rate = SPEEDS[si];
    localStorage.setItem('ttsrate', rate); speedBtn.textContent = speedLabel();
    if (active && !paused) { gen++; synth.cancel(); setTimeout(speakCur, 60); }
  }

  function visibleIndex() {                                   // first prayer in view
    for (var i = 0; i < items.length; i++)
      if (items[i].getBoundingClientRect().bottom > 90) return i;
    return 0;
  }
  function startFromView() { startAt(visibleIndex()); }

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
    u.rate = rate; u.pitch = 1;
    u.onend = function () { if (g !== gen) return; cur++; if (cur < items.length) speakCur(); else stop(); };
    u.onerror = function () { if (g !== gen) return; cur++; if (cur < items.length) speakCur(); else stop(); };
    synth.speak(u);
  }
  function startAt(idx) {
    gen++; synth.cancel(); cur = idx; active = true; setPaused(false);
    bar.hidden = false; fab.hidden = true;
    document.documentElement.classList.add('tts-on');
    setTimeout(speakCur, 60);
  }
  function stop() {
    gen++; active = false; setPaused(false); synth.cancel();
    items.forEach(function (el) { el.classList.remove('speaking'); });
    bar.hidden = true; fab.hidden = false;
    document.documentElement.classList.remove('tts-on');
  }
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
    else if (a === 'speed') cycleSpeed();
  });
  window.addEventListener('pagehide', function () { try { synth.cancel(); } catch (e) {} });
})();
