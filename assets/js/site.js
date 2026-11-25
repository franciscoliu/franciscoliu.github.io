/* Small progressive enhancements. The pages are complete without this file:
   every publication and news item is in the HTML; scripts only hide, filter and count. */
(function () {
  'use strict';

  /* ---- Home: show the five most recent news items, reveal the rest on request ---- */
  var news = document.querySelector('.news[data-collapse]');
  var newsButton = document.querySelector('[data-news-toggle]');
  if (news && newsButton) {
    var keep = parseInt(news.getAttribute('data-collapse'), 10) || 5;
    var extra = Array.prototype.slice.call(news.children, keep);
    var open = false;
    var paint = function () {
      extra.forEach(function (li) { li.hidden = !open; });
      newsButton.textContent = open ? 'Show less' : 'Show more news';
      newsButton.setAttribute('aria-expanded', String(open));
    };
    if (extra.length) {
      newsButton.hidden = false;
      newsButton.addEventListener('click', function () { open = !open; paint(); });
      paint();
    }
  }

  /* ---- Publications: Selected / All and topic filters ---- */
  var list = document.getElementById('publication-list');
  if (!list) return;
  var pubs = Array.prototype.slice.call(list.querySelectorAll('.pub'));
  var scopeChips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-scope]'));
  var topicChips = Array.prototype.slice.call(document.querySelectorAll('.chip[data-topic]'));
  var empty = document.getElementById('publication-empty');
  var state = { scope: 'selected', topic: 'all' };

  function inScope(pub) { return state.scope === 'all' || pub.getAttribute('data-selected') === 'true'; }
  function inTopic(pub, topic) { return topic === 'all' || pub.getAttribute('data-topic') === topic; }

  function paintPubs() {
    var shown = 0;
    pubs.forEach(function (pub) {
      var show = inScope(pub) && inTopic(pub, state.topic);
      pub.hidden = !show;
      if (show) shown += 1;
    });
    scopeChips.forEach(function (chip) {
      var scope = chip.getAttribute('data-scope');
      chip.setAttribute('aria-pressed', String(scope === state.scope));
      var n = chip.querySelector('.n');
      if (n) n.textContent = pubs.filter(function (p) { return scope === 'all' || p.getAttribute('data-selected') === 'true'; }).length;
    });
    topicChips.forEach(function (chip) {
      var topic = chip.getAttribute('data-topic');
      chip.setAttribute('aria-pressed', String(topic === state.topic));
      var n = chip.querySelector('.n');
      if (n) n.textContent = pubs.filter(function (p) { return inScope(p) && inTopic(p, topic); }).length;
    });
    if (empty) empty.hidden = shown !== 0;
  }

  scopeChips.forEach(function (chip) {
    chip.addEventListener('click', function () { state.scope = chip.getAttribute('data-scope'); paintPubs(); });
  });
  topicChips.forEach(function (chip) {
    chip.addEventListener('click', function () { state.topic = chip.getAttribute('data-topic'); paintPubs(); });
  });

  /* A link such as publications.html#some-paper or ?topic=action should always land on a visible entry. */
  var params = new URLSearchParams(window.location.search);
  var wanted = params.get('topic');
  if (wanted && topicChips.some(function (c) { return c.getAttribute('data-topic') === wanted; })) state.topic = wanted;
  if (params.get('scope') === 'all') state.scope = 'all';
  var target = window.location.hash ? document.getElementById(decodeURIComponent(window.location.hash.slice(1))) : null;
  if (target && target.classList.contains('pub')) {
    if (target.getAttribute('data-selected') !== 'true') state.scope = 'all';
    state.topic = 'all';
  }
  paintPubs();
  if (target && target.classList.contains('pub')) target.scrollIntoView();
})();
