(function () {
  const hour = new Date().getHours();
  const body = document.body;
  let mode = 'ui-day';
  if (hour >= 20 || hour < 5) {
    mode = 'ui-night';
  } else if ((hour >= 5 && hour < 8) || (hour >= 17 && hour < 20)) {
    mode = 'ui-twilight';
  }
  body.classList.remove('ui-day', 'ui-twilight', 'ui-night');
  body.classList.add(mode);
})();
