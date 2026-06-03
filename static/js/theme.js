(function () {
  const body = document.body;
  const themeToggle = document.getElementById('theme-toggle');
  const themeIcon = document.getElementById('theme-icon');

  // Theme modes
  const themes = {
    'ui-day': { name: 'day', icon: '☀️', next: 'ui-twilight' },
    'ui-twilight': { name: 'twilight', icon: '🌅', next: 'ui-night' },
    'ui-night': { name: 'night', icon: '🌙', next: 'ui-day' }
  };

  // Get saved theme or auto-detect
  function getInitialTheme() {
    const saved = localStorage.getItem('snorkelforecast-theme');
    if (saved && themes[saved]) {
      return saved;
    }

    // Auto-detect based on time
    const hour = new Date().getHours();
    if (hour >= 20 || hour < 5) {
      return 'ui-night';
    } else if ((hour >= 5 && hour < 8) || (hour >= 17 && hour < 20)) {
      return 'ui-twilight';
    }
    return 'ui-day';
  }

  // Apply theme
  function applyTheme(theme) {
    body.classList.remove('ui-day', 'ui-twilight', 'ui-night');
    body.classList.add(theme);

    // Update toggle button
    if (themeToggle && themeIcon) {
      themeIcon.textContent = themes[theme].icon;
      themeToggle.setAttribute('aria-label', `Switch to ${themes[themes[theme].next].name} mode`);
    }

    // Update theme-color meta tag
    const themeColorMeta = document.getElementById('theme-color');
    if (themeColorMeta) {
      const colors = {
        'ui-day': '#cfe9ea',      // sunlit shallows
        'ui-twilight': '#3a2450', // golden hour
        'ui-night': '#041d29'     // abyss
      };
      themeColorMeta.content = colors[theme] || '#041d29';
    }

    // Save preference
    localStorage.setItem('snorkelforecast-theme', theme);
  }

  // Initialize theme
  const initialTheme = getInitialTheme();
  applyTheme(initialTheme);

  // Handle manual toggle
  if (themeToggle) {
    themeToggle.addEventListener('click', function() {
      const currentTheme = Array.from(body.classList).find(cls => themes[cls]);
      const nextTheme = themes[currentTheme].next;
      applyTheme(nextTheme);
    });
  }
})();
