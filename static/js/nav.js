(function () {
  const toggle = document.getElementById('menu-toggle');
  const panel = document.getElementById('mobile-menu');
  if (!toggle || !panel) return;

  function setExpanded(expanded) {
    toggle.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    panel.classList.toggle('hidden', !expanded);
  }

  let open = false;
  toggle.addEventListener('click', function () {
    open = !open;
    setExpanded(open);
  });

  // Close when a menu link is clicked
  panel.querySelectorAll('a').forEach(function (a) {
    a.addEventListener('click', function () {
      open = false;
      setExpanded(false);
    });
  });

  // Click outside closes the panel
  document.addEventListener('click', function (e) {
    if (!open) return;
    if (panel.contains(e.target) || toggle.contains(e.target)) return;
    open = false;
    setExpanded(false);
  });

  // Close on Escape
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && open) {
      open = false;
      setExpanded(false);
      toggle.focus();
    }
  });
})();
