(function() {
  var themes = ['coral', 'purple', 'amber', 'pink'];
  var accents = ['#FF4500', '#8B6BFF', '#FFB300', '#FF4DB8'];
  var labels = ['Coral', 'Purple', 'Amber', 'Pink'];
  var idx = 0;

  function set(i) {
    document.documentElement.style.setProperty('--accent', accents[i]);
    var btn = document.getElementById('theme-toggle');
    if (btn) btn.textContent = labels[i];
    try { localStorage.setItem('shopbot-accent', i); } catch(e) {}
  }

  function init() {
    if (document.getElementById('theme-toggle')) return;
    try { idx = parseInt(localStorage.getItem('shopbot-accent')) || 0; } catch(e) {}
    if (idx < 0 || idx >= themes.length) idx = 0;

    var btn = document.createElement('button');
    btn.id = 'theme-toggle';
    btn.textContent = labels[idx];
    btn.onclick = function() { idx = (idx + 1) % themes.length; set(idx); };
    document.body.appendChild(btn);
    set(idx);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
    setTimeout(init, 500);
  }
})();
